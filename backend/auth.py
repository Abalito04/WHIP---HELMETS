import bcrypt
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g
from database import get_conn


class AuthManager:
    def __init__(self):
        pass  # PostgreSQL se inicializa en database.py

    # ---------------------- PASSWORDS ----------------------

    def hash_password(self, password):
        """Hash de contraseña usando bcrypt con sal aleatoria"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, password, hashed):
        """Soporta bcrypt (nuevo) y SHA-256 (usuarios legacy)"""
        if hashed.startswith('$2b$') or hashed.startswith('$2a$'):
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        # Hash SHA-256 legacy — migración automática
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest() == hashed

    def _migrate_password_to_bcrypt(self, user_id, password):
        """Migrar SHA-256 a bcrypt automáticamente al hacer login exitoso"""
        try:
            new_hash = self.hash_password(password)
            with get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE users SET password_hash = %s WHERE id = %s",
                    (new_hash, user_id)
                )
                conn.commit()
        except Exception as e:
            print(f"⚠️ Error migrando hash de contraseña: {e}")

    # ---------------------- SESIONES ----------------------

    def generate_token(self):
        """Generar token de sesión"""
        return secrets.token_urlsafe(32)

    def create_session(self, user_id, expires_hours=24):
        """Crear sesión de usuario"""
        token = self.generate_token()
        expires_at = datetime.now() + timedelta(hours=expires_hours)

        with get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sessions (user_id, token, expires_at) VALUES (%s, %s, %s)",
                (user_id, token, expires_at)
            )
            conn.commit()

        return token

    def validate_session(self, token):
        """Validar sesión y obtener usuario"""
        with get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE expires_at < NOW()")
            cursor.execute(
                """
                SELECT u.id, u.username, u.role, u.nombre, u.apellido, u.email
                FROM users u
                JOIN sessions s ON u.id = s.user_id
                WHERE s.token = %s AND s.expires_at > NOW()
                """,
                (token,)
            )
            user = cursor.fetchone()

            if user:
                conn.commit()
                return {
                    'user_id': user['id'],
                    'username': user['username'],
                    'role': user['role'],
                    'nombre': user['nombre'],
                    'apellido': user['apellido'],
                    'email': user['email']
                }

        return None

    # ---------------------- REGISTRO ----------------------

    def register_user(self, username, password, email=None, nombre=None, apellido=None,
                      dni=None, telefono=None, direccion=None, codigo_postal=None):
        """Registrar nuevo usuario"""
        try:
            with get_conn() as conn:
                cursor = conn.cursor()

                # Verificar duplicados
                cursor.execute(
                    "SELECT id FROM users WHERE username = %s OR email = %s OR dni = %s OR telefono = %s",
                    (username, email, dni, telefono)
                )
                if cursor.fetchone():
                    cursor.execute(
                        "SELECT username, email, dni, telefono FROM users WHERE username = %s OR email = %s OR dni = %s OR telefono = %s",
                        (username, email, dni, telefono)
                    )
                    dup = cursor.fetchone()
                    if dup:
                        if dup['username'] == username:
                            return {"success": False, "error": "El nombre de usuario ya está en uso"}
                        elif dup['email'] == email:
                            return {"success": False, "error": "El email ya está registrado"}
                        elif dup['dni'] == dni:
                            return {"success": False, "error": "El DNI ya está registrado"}
                        elif dup['telefono'] == telefono:
                            return {"success": False, "error": "El teléfono ya está registrado"}
                    return {"success": False, "error": "Los datos proporcionados ya están en uso"}

                password_hash = self.hash_password(password)

                cursor.execute(
                    """
                    INSERT INTO users (username, password_hash, email, nombre, apellido,
                                       dni, telefono, direccion, codigo_postal, role)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (username, password_hash, email, nombre, apellido,
                     dni, telefono, direccion, codigo_postal, 'user')
                )
                result = cursor.fetchone()
                conn.commit()

                user_id = result['id'] if isinstance(result, dict) else result[0]
                return {"success": True, "message": "Usuario registrado correctamente", "user_id": user_id}

        except Exception as e:
            print(f"❌ Error en register_user: {type(e).__name__} - {str(e)}")
            return {"success": False, "error": f"Error al registrar usuario: {str(e)}"}

    # ---------------------- AUTENTICACIÓN ----------------------

    def authenticate_user(self, username, password):
        """Autenticar usuario"""
        try:
            with get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, username, password_hash, role, email_verified FROM users WHERE username = %s",
                    (username,)
                )
                user = cursor.fetchone()

                if not user:
                    return None

                if not self.verify_password(password, user['password_hash']):
                    return None

                # Migrar a bcrypt si el hash es SHA-256 legacy
                if not (user['password_hash'].startswith('$2b$') or user['password_hash'].startswith('$2a$')):
                    self._migrate_password_to_bcrypt(user['id'], password)

                email_verified = user.get('email_verified', False)

                if not email_verified:
                    return {
                        'id': user['id'],
                        'username': user['username'],
                        'role': user['role'],
                        'email_verified': False,
                        'error': 'email_not_verified'
                    }

                return {
                    'id': user['id'],
                    'username': user['username'],
                    'role': user['role'],
                    'email_verified': True
                }

        except Exception as e:
            print(f"❌ Error en authenticate_user: {type(e).__name__} - {str(e)}")
            return None

    def login(self, username, password):
        """Login de usuario con creación de sesión"""
        try:
            user = self.authenticate_user(username, password)

            if not user:
                return {'success': False, 'error': 'Credenciales inválidas'}

            if user.get('error') == 'email_not_verified':
                return {
                    'success': False,
                    'error': 'email_not_verified',
                    'message': 'Debes verificar tu email antes de poder iniciar sesión. Revisa tu bandeja de entrada.'
                }

            token = self.create_session(user['id'])
            user_data = self.get_user_by_id(user['id'])

            return {
                'success': True,
                'message': 'Login exitoso',
                'session_token': token,
                'user': user_data
            }

        except Exception as e:
            print(f"❌ Error en login: {type(e).__name__} - {str(e)}")
            return {'success': False, 'error': f'Error al hacer login: {str(e)}'}

    def logout_user(self, token):
        """Cerrar sesión"""
        with get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE token = %s", (token,))
            conn.commit()

    def logout(self, token):
        """Logout de usuario"""
        try:
            self.logout_user(token)
            return {'success': True, 'message': 'Logout exitoso'}
        except Exception as e:
            return {'success': False, 'error': f'Error al hacer logout: {str(e)}'}

    # ---------------------- USUARIOS ----------------------

    def get_users(self):
        """Obtener lista de usuarios (solo admin)"""
        with get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, role, created_at FROM users ORDER BY created_at DESC")
            users = cursor.fetchall()
            return [
                {
                    'id': u['id'],
                    'username': u['username'],
                    'role': u['role'],
                    'created_at': u['created_at'].isoformat() if u['created_at'] else None
                }
                for u in users
            ]

    def get_user_by_id(self, user_id):
        """Obtener usuario por ID"""
        with get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, username, role, nombre, apellido, dni, telefono,
                       direccion, codigo_postal, email, created_at, updated_at
                FROM users WHERE id = %s
                """,
                (user_id,)
            )
            user = cursor.fetchone()
            if user:
                return {
                    'id': user['id'],
                    'username': user['username'],
                    'role': user['role'],
                    'nombre': user['nombre'],
                    'apellido': user['apellido'],
                    'dni': user['dni'],
                    'telefono': user['telefono'],
                    'direccion': user['direccion'],
                    'codigo_postal': user['codigo_postal'],
                    'email': user['email'],
                    'created_at': user['created_at'].isoformat() if user['created_at'] else None,
                    'updated_at': user['updated_at'].isoformat() if user['updated_at'] else None
                }
        return None

    def update_user_profile(self, user_id, data):
        """Actualizar perfil de usuario"""
        try:
            with get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
                if not cursor.fetchone():
                    return {"success": False, "error": "Usuario no encontrado"}

                allowed_fields = ['nombre', 'apellido', 'dni', 'telefono', 'direccion', 'codigo_postal', 'email']
                update_fields, values = [], []
                for field in allowed_fields:
                    if field in data:
                        update_fields.append(f"{field} = %s")
                        values.append(data[field])

                if update_fields:
                    values.append(user_id)
                    cursor.execute(
                        f"UPDATE users SET {', '.join(update_fields)}, updated_at = NOW() WHERE id = %s",
                        values
                    )
                    conn.commit()

                return {"success": True, "message": "Perfil actualizado correctamente"}

        except Exception as e:
            return {"success": False, "error": f"Error al actualizar perfil: {str(e)}"}

    def get_all_users(self):
        """Obtener todos los usuarios (para admin)"""
        try:
            with get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, username, role, nombre, apellido, dni, telefono,
                           direccion, codigo_postal, email, created_at, updated_at
                    FROM users ORDER BY created_at DESC
                    """
                )
                users = cursor.fetchall()
                return [
                    {
                        'id': u['id'],
                        'username': u['username'],
                        'role': u['role'],
                        'nombre': u['nombre'],
                        'apellido': u['apellido'],
                        'dni': u['dni'],
                        'telefono': u['telefono'],
                        'direccion': u['direccion'],
                        'codigo_postal': u['codigo_postal'],
                        'email': u['email'],
                        'created_at': u['created_at'].isoformat() if u['created_at'] else None,
                        'updated_at': u['updated_at'].isoformat() if u['updated_at'] else None
                    }
                    for u in users
                ]
        except Exception as e:
            print(f"❌ Error en get_all_users: {str(e)}")
            return []

    def update_user_role(self, user_id, new_role):
        """Actualizar rol de usuario (solo admin)"""
        try:
            with get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
                if not cursor.fetchone():
                    return {"success": False, "error": "Usuario no encontrado"}
                cursor.execute(
                    "UPDATE users SET role = %s, updated_at = NOW() WHERE id = %s",
                    (new_role, user_id)
                )
                conn.commit()
                return {"success": True, "message": "Rol actualizado correctamente"}
        except Exception as e:
            return {"success": False, "error": f"Error al actualizar rol: {str(e)}"}

    def delete_user(self, user_id):
        """Eliminar usuario (solo admin)"""
        try:
            with get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
                if not cursor.fetchone():
                    return {"success": False, "error": "Usuario no encontrado"}
                cursor.execute("DELETE FROM sessions WHERE user_id = %s", (user_id,))
                cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
                conn.commit()
                return {"success": True, "message": "Usuario eliminado correctamente"}
        except Exception as e:
            return {"success": False, "error": f"Error al eliminar usuario: {str(e)}"}

    def update_user_by_admin(self, user_id, data):
        """Actualizar usuario por admin"""
        try:
            with get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
                if not cursor.fetchone():
                    return {"success": False, "error": "Usuario no encontrado"}

                if any(f in data for f in ['username', 'email', 'dni', 'telefono']):
                    cursor.execute(
                        "SELECT id, username, email, dni, telefono FROM users WHERE (username = %s OR email = %s OR dni = %s OR telefono = %s) AND id != %s",
                        (data.get('username'), data.get('email'), data.get('dni'), data.get('telefono'), user_id)
                    )
                    dup = cursor.fetchone()
                    if dup:
                        if dup['username'] == data.get('username'):
                            return {"success": False, "error": "El nombre de usuario ya está en uso"}
                        elif dup['email'] == data.get('email'):
                            return {"success": False, "error": "El email ya está registrado"}
                        elif dup['dni'] == data.get('dni'):
                            return {"success": False, "error": "El DNI ya está registrado"}
                        elif dup['telefono'] == data.get('telefono'):
                            return {"success": False, "error": "El teléfono ya está registrado"}

                allowed_fields = ['username', 'email', 'nombre', 'apellido', 'dni',
                                   'telefono', 'direccion', 'codigo_postal', 'role']
                update_fields, values = [], []
                for field in allowed_fields:
                    if field in data:
                        update_fields.append(f"{field} = %s")
                        values.append(data[field])

                if update_fields:
                    values.append(user_id)
                    cursor.execute(
                        f"UPDATE users SET {', '.join(update_fields)}, updated_at = NOW() WHERE id = %s",
                        values
                    )
                    conn.commit()

                return {"success": True, "message": "Usuario actualizado correctamente"}

        except Exception as e:
            return {"success": False, "error": f"Error al actualizar usuario: {str(e)}"}

    def create_user_by_admin(self, data):
        """Crear usuario por admin"""
        try:
            with get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id FROM users WHERE username = %s OR email = %s OR dni = %s OR telefono = %s",
                    (data.get('username'), data.get('email'), data.get('dni'), data.get('telefono'))
                )
                if cursor.fetchone():
                    cursor.execute(
                        "SELECT username, email, dni, telefono FROM users WHERE username = %s OR email = %s OR dni = %s OR telefono = %s",
                        (data.get('username'), data.get('email'), data.get('dni'), data.get('telefono'))
                    )
                    dup = cursor.fetchone()
                    if dup:
                        if dup['username'] == data.get('username'):
                            return {"success": False, "error": "El nombre de usuario ya está en uso"}
                        elif dup['email'] == data.get('email'):
                            return {"success": False, "error": "El email ya está registrado"}
                        elif dup['dni'] == data.get('dni'):
                            return {"success": False, "error": "El DNI ya está registrado"}
                        elif dup['telefono'] == data.get('telefono'):
                            return {"success": False, "error": "El teléfono ya está registrado"}
                    return {"success": False, "error": "Los datos proporcionados ya están en uso"}

                password_hash = self.hash_password(data.get('password', 'temp123'))
                cursor.execute(
                    """
                    INSERT INTO users (username, password_hash, email, nombre, apellido,
                                       dni, telefono, direccion, codigo_postal, role)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (data.get('username'), password_hash, data.get('email'), data.get('nombre'),
                     data.get('apellido'), data.get('dni'), data.get('telefono'),
                     data.get('direccion'), data.get('codigo_postal'), data.get('role', 'user'))
                )
                conn.commit()
                return {"success": True, "message": "Usuario creado correctamente"}

        except Exception as e:
            return {"success": False, "error": f"Error al crear usuario: {str(e)}"}


# Instancia global
auth_manager = AuthManager()


# ---------------------- DECORADORES ----------------------

def require_auth(f):
    """Decorator para requerir autenticación"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": "Token de autorización requerido"}), 401
        if token.startswith('Bearer '):
            token = token[7:]
        user = auth_manager.validate_session(token)
        if not user:
            return jsonify({"error": "Token inválido o expirado"}), 401
        g.current_user = user
        return f(*args, **kwargs)
    return decorated_function


def require_admin(f):
    """Decorator para requerir rol de administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": "Token de autorización requerido"}), 401
        if token.startswith('Bearer '):
            token = token[7:]
        user = auth_manager.validate_session(token)
        if not user:
            return jsonify({"error": "Token inválido o expirado"}), 401
        if user.get('role') != 'admin':
            return jsonify({"error": "Se requiere rol de administrador"}), 403
        g.current_user = user
        return f(*args, **kwargs)
    return decorated_function
