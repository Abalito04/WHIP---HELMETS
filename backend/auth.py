import hashlib
import secrets
import time
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g
from database import get_conn

class AuthManager:
    def __init__(self):
        pass  # PostgreSQL se inicializa en database.py
    
    def hash_password(self, password):
        """Hash de contraseña usando SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password, hashed):
        """Verificar contraseña"""
        return self.hash_password(password) == hashed
    
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
            # Limpiar sesiones expiradas
            cursor.execute("DELETE FROM sessions WHERE expires_at < NOW()")
            
            # Buscar sesión válida
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
    
    def register_user(self, username, password, email=None, nombre=None, apellido=None, dni=None, telefono=None, direccion=None, codigo_postal=None):
        """Registrar nuevo usuario"""
        try:
            with get_conn() as conn:
                cursor = conn.cursor()
                # Verificar si el usuario ya existe (username, email, DNI, teléfono)
                cursor.execute(
                    "SELECT id FROM users WHERE username = %s OR email = %s OR dni = %s OR telefono = %s",
                    (username, email, dni, telefono)
                )
                existing_user = cursor.fetchone()
                
                if existing_user:
                    # Verificar cuál campo específico está duplicado
                    cursor.execute(
                        "SELECT username, email, dni, telefono FROM users WHERE username = %s OR email = %s OR dni = %s OR telefono = %s",
                        (username, email, dni, telefono)
                    )
                    duplicate_data = cursor.fetchone()
                    
                    if duplicate_data:
                        if duplicate_data['username'] == username:
                            return {"success": False, "error": "El nombre de usuario ya está en uso"}
                        elif duplicate_data['email'] == email:
                            return {"success": False, "error": "El email ya está registrado"}
                        elif duplicate_data['dni'] == dni:
                            return {"success": False, "error": "El DNI ya está registrado"}
                        elif duplicate_data['telefono'] == telefono:
                            return {"success": False, "error": "El teléfono ya está registrado"}
                    
                    return {"success": False, "error": "Los datos proporcionados ya están en uso"}
                
                # Crear usuario
                password_hash = self.hash_password(password)
                cursor.execute(
                    """
                    INSERT INTO users (username, password_hash, email, nombre, apellido, dni, telefono, direccion, codigo_postal, role)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (username, password_hash, email, nombre, apellido, dni, telefono, direccion, codigo_postal, 'user')
                )
                conn.commit()
                
                # Obtener el ID del usuario recién creado
                cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
                user_result = cursor.fetchone()
                user_id = user_result[0] if user_result else None
                
                return {"success": True, "message": "Usuario registrado correctamente", "user_id": user_id}
                
        except Exception as e:
            return {"success": False, "error": f"Error al registrar usuario: {str(e)}"}
    
    def authenticate_user(self, username, password):
        """Autenticar usuario"""
        try:
            print(f"DEBUG: Autenticando usuario: {username}")
            with get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, username, password_hash, role, email_verified FROM users WHERE username = %s",
                    (username,)
                )
                user = cursor.fetchone()
                print(f"DEBUG: Usuario encontrado en DB: {user}")
                
                if user:
                    print(f"DEBUG: Verificando contraseña...")
                    print(f"DEBUG: Tipo de user: {type(user)}")
                    print(f"DEBUG: Contenido de user: {user}")
                    
                    # Acceder a los datos usando nombres de columna (RealDictRow)
                    password_valid = self.verify_password(password, user['password_hash'])
                    print(f"DEBUG: Contraseña válida: {password_valid}")
                    
                    if password_valid:
                        # Verificar si el email está verificado
                        email_verified = user.get('email_verified', False)
                        print(f"DEBUG: Email verificado: {email_verified}")
                        
                        if not email_verified:
                            print(f"DEBUG: Email no verificado para usuario: {username}")
                            return {
                                'id': user['id'],
                                'username': user['username'],
                                'role': user['role'],
                                'email_verified': False,
                                'error': 'email_not_verified'
                            }
                        
                        result = {
                            'id': user['id'],
                            'username': user['username'],
                            'role': user['role'],
                            'email_verified': True
                        }
                        print(f"DEBUG: Usuario autenticado exitosamente: {result}")
                        return result
                    else:
                        print(f"DEBUG: Contraseña incorrecta para usuario: {username}")
                else:
                    print(f"DEBUG: Usuario no encontrado: {username}")
                
        except Exception as e:
            print(f"DEBUG: Error en authenticate_user: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return None
    
    def login(self, username, password):
        """Login de usuario con creación de sesión"""
        try:
            print(f"DEBUG: Intentando login para usuario: {username}")
            
            # Autenticar usuario
            user = self.authenticate_user(username, password)
            print(f"DEBUG: Resultado de autenticación: {user}")
            
            if user:
                # Verificar si hay error de email no verificado
                if user.get('error') == 'email_not_verified':
                    print(f"DEBUG: Email no verificado para usuario: {username}")
                    return {
                        'success': False,
                        'error': 'email_not_verified',
                        'message': 'Debes verificar tu email antes de poder iniciar sesión. Revisa tu bandeja de entrada.'
                    }
                
                print(f"DEBUG: Usuario autenticado, creando sesión para ID: {user['id']}")
                
                # Crear sesión
                token = self.create_session(user['id'])
                print(f"DEBUG: Token creado: {token[:10]}...")
                
                # Obtener datos completos del usuario
                user_data = self.get_user_by_id(user['id'])
                print(f"DEBUG: Datos del usuario: {user_data}")
                
                return {
                    'success': True,
                    'message': 'Login exitoso',
                    'session_token': token,
                    'user': user_data
                    }
            else:
                print(f"DEBUG: Autenticación fallida para usuario: {username}")
                return {
                    'success': False,
                    'error': 'Credenciales inválidas'
                }
                
        except Exception as e:
            print(f"DEBUG: Error en login: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f'Error al hacer login: {str(e)}'
            }
    
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
            return {
                'success': True,
                'message': 'Logout exitoso'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error al hacer logout: {str(e)}'
            }
    
    def get_users(self):
        """Obtener lista de usuarios (solo admin)"""
        with get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, role, created_at FROM users ORDER BY created_at DESC"
            )
            users = cursor.fetchall()
            
            return [
                {
                    'id': user['id'],
                    'username': user['username'],
                    'role': user['role'],
                    'created_at': user['created_at'].isoformat() if user['created_at'] else None
                }
                for user in users
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
                
                # Verificar si el usuario existe
                cursor.execute(
                    "SELECT id FROM users WHERE id = %s",
                    (user_id,)
                )
                user_exists = cursor.fetchone()
                
                if not user_exists:
                    return {"success": False, "error": "Usuario no encontrado"}
                
                # Actualizar campos permitidos
                allowed_fields = ['nombre', 'apellido', 'dni', 'telefono', 'direccion', 'codigo_postal', 'email']
                update_fields = []
                values = []
                
                for field in allowed_fields:
                    if field in data:
                        update_fields.append(f"{field} = %s")
                        values.append(data[field])
                
                if update_fields:
                    values.append(user_id)
                    query = f"UPDATE users SET {', '.join(update_fields)}, updated_at = NOW() WHERE id = %s"
                    cursor.execute(query, values)
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
                    for user in users
                ]
        except Exception as e:
            print(f"DEBUG: Error en get_all_users: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    def update_user_role(self, user_id, new_role):
        """Actualizar rol de usuario (solo admin)"""
        try:
            with get_conn() as conn:
                cursor = conn.cursor()
                # Verificar si el usuario existe
                cursor.execute(
                    "SELECT id FROM users WHERE id = %s",
                    (user_id,)
                )
                user_exists = cursor.fetchone()
                
                if not user_exists:
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
                # Verificar si el usuario existe
                cursor.execute(
                    "SELECT id FROM users WHERE id = %s",
                    (user_id,)
                )
                user_exists = cursor.fetchone()
                
                if not user_exists:
                    return {"success": False, "error": "Usuario no encontrado"}
                
                # Eliminar sesiones del usuario
                cursor.execute("DELETE FROM sessions WHERE user_id = %s", (user_id,))
                # Eliminar usuario
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
                
                # Verificar si el usuario existe
                cursor.execute(
                    "SELECT id FROM users WHERE id = %s",
                    (user_id,)
                )
                user_exists = cursor.fetchone()
                
                if not user_exists:
                    return {"success": False, "error": "Usuario no encontrado"}
                
                # Verificar unicidad de campos críticos (excluyendo el usuario actual)
                if any(field in data for field in ['username', 'email', 'dni', 'telefono']):
                    cursor.execute(
                        "SELECT id, username, email, dni, telefono FROM users WHERE (username = %s OR email = %s OR dni = %s OR telefono = %s) AND id != %s",
                        (data.get('username'), data.get('email'), data.get('dni'), data.get('telefono'), user_id)
                    )
                    duplicate_user = cursor.fetchone()
                    
                    if duplicate_user:
                        if duplicate_user['username'] == data.get('username'):
                            return {"success": False, "error": "El nombre de usuario ya está en uso"}
                        elif duplicate_user['email'] == data.get('email'):
                            return {"success": False, "error": "El email ya está registrado"}
                        elif duplicate_user['dni'] == data.get('dni'):
                            return {"success": False, "error": "El DNI ya está registrado"}
                        elif duplicate_user['telefono'] == data.get('telefono'):
                            return {"success": False, "error": "El teléfono ya está registrado"}
                
                # Actualizar campos permitidos
                allowed_fields = ['username', 'email', 'nombre', 'apellido', 'dni', 'telefono', 'direccion', 'codigo_postal', 'role']
                update_fields = []
                values = []
                
                for field in allowed_fields:
                    if field in data:
                        update_fields.append(f"{field} = %s")
                        values.append(data[field])
                
                if update_fields:
                    values.append(user_id)
                    query = f"UPDATE users SET {', '.join(update_fields)}, updated_at = NOW() WHERE id = %s"
                    cursor.execute(query, values)
                    conn.commit()
                
                return {"success": True, "message": "Usuario actualizado correctamente"}
                
        except Exception as e:
            return {"success": False, "error": f"Error al actualizar usuario: {str(e)}"}

    def create_user_by_admin(self, data):
        """Crear usuario por admin"""
        try:
            with get_conn() as conn:
                cursor = conn.cursor()
                
                # Verificar si el usuario ya existe (username, email, DNI, teléfono)
                cursor.execute(
                    "SELECT id FROM users WHERE username = %s OR email = %s OR dni = %s OR telefono = %s",
                    (data.get('username'), data.get('email'), data.get('dni'), data.get('telefono'))
                )
                existing_user = cursor.fetchone()
                
                if existing_user:
                    # Verificar cuál campo específico está duplicado
                    cursor.execute(
                        "SELECT username, email, dni, telefono FROM users WHERE username = %s OR email = %s OR dni = %s OR telefono = %s",
                        (data.get('username'), data.get('email'), data.get('dni'), data.get('telefono'))
                    )
                    duplicate_data = cursor.fetchone()
                    
                    if duplicate_data:
                        if duplicate_data['username'] == data.get('username'):
                            return {"success": False, "error": "El nombre de usuario ya está en uso"}
                        elif duplicate_data['email'] == data.get('email'):
                            return {"success": False, "error": "El email ya está registrado"}
                        elif duplicate_data['dni'] == data.get('dni'):
                            return {"success": False, "error": "El DNI ya está registrado"}
                        elif duplicate_data['telefono'] == data.get('telefono'):
                            return {"success": False, "error": "El teléfono ya está registrado"}
                    
                    return {"success": False, "error": "Los datos proporcionados ya están en uso"}
                
                # Crear usuario
                password_hash = self.hash_password(data.get('password', 'temp123'))
                cursor.execute(
                    """
                    INSERT INTO users (username, password_hash, email, nombre, apellido, dni, telefono, direccion, codigo_postal, role)
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

# Instancia global del manager de autenticación
auth_manager = AuthManager()

def require_auth(f):
    """Decorator para requerir autenticación"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": "Token de autorización requerido"}), 401
        
        # Remover "Bearer " si está presente
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
        
        # Remover "Bearer " si está presente
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