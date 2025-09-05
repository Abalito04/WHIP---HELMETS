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
                    'user_id': user[0],
                    'username': user[1],
                    'role': user[2],
                    'nombre': user[3],
                    'apellido': user[4],
                    'email': user[5]
                }
        
        return None
    
    def register_user(self, username, password, email=None, nombre=None, apellido=None, dni=None, telefono=None, direccion=None, codigo_postal=None):
        """Registrar nuevo usuario"""
        try:
            with get_conn() as conn:
                cursor = conn.cursor()
                # Verificar si el usuario ya existe
                existing_user = cursor.execute(
                    "SELECT id FROM users WHERE username = %s OR email = %s",
                    (username, email)
                ).fetchone()
                
                if existing_user:
                    return {"success": False, "error": "El usuario o email ya existe"}
                
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
                return {"success": True, "message": "Usuario registrado correctamente"}
                
        except Exception as e:
            return {"success": False, "error": f"Error al registrar usuario: {str(e)}"}
    
    def authenticate_user(self, username, password):
        """Autenticar usuario"""
        with get_conn() as conn:
            cursor = conn.cursor()
            user = cursor.execute(
                "SELECT id, username, password_hash, role FROM users WHERE username = %s",
                (username,)
            ).fetchone()
            
            if user and self.verify_password(password, user[2]):
                return {
                    'id': user[0],
                    'username': user[1],
                    'role': user[3]
                }
        
        return None
    
    def logout_user(self, token):
        """Cerrar sesión"""
        with get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE token = %s", (token,))
            conn.commit()
    
    def get_users(self):
        """Obtener lista de usuarios (solo admin)"""
        with get_conn() as conn:
            cursor = conn.cursor()
            users = cursor.execute(
                "SELECT id, username, role, created_at FROM users ORDER BY created_at DESC"
            ).fetchall()
            
            return [
                {
                    'id': user[0],
                    'username': user[1],
                    'role': user[2],
                    'created_at': user[3].isoformat() if user[3] else None
                }
                for user in users
            ]
    
    def get_user_by_id(self, user_id):
        """Obtener usuario por ID"""
        with get_conn() as conn:
            cursor = conn.cursor()
            user = cursor.execute(
                """
                SELECT id, username, role, nombre, apellido, dni, telefono, 
                       direccion, codigo_postal, email, created_at, updated_at
                FROM users WHERE id = %s
                """,
                (user_id,)
            ).fetchone()
            
            if user:
                return {
                    'id': user[0],
                    'username': user[1],
                    'role': user[2],
                    'nombre': user[3],
                    'apellido': user[4],
                    'dni': user[5],
                    'telefono': user[6],
                    'direccion': user[7],
                    'codigo_postal': user[8],
                    'email': user[9],
                    'created_at': user[10].isoformat() if user[10] else None,
                    'updated_at': user[11].isoformat() if user[11] else None
                }
        
        return None
    
    def update_user_profile(self, user_id, data):
        """Actualizar perfil de usuario"""
        try:
            with get_conn() as conn:
                cursor = conn.cursor()
                
                # Verificar si el usuario existe
                user_exists = cursor.execute(
                    "SELECT id FROM users WHERE id = %s",
                    (user_id,)
                ).fetchone()
                
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
        with get_conn() as conn:
            cursor = conn.cursor()
            users = cursor.execute(
                """
                SELECT id, username, role, nombre, apellido, dni, telefono, 
                       direccion, codigo_postal, email, created_at, updated_at
                FROM users ORDER BY created_at DESC
                """
            ).fetchall()
            
            return [
                {
                    'id': user[0],
                    'username': user[1],
                    'role': user[2],
                    'nombre': user[3],
                    'apellido': user[4],
                    'dni': user[5],
                    'telefono': user[6],
                    'direccion': user[7],
                    'codigo_postal': user[8],
                    'email': user[9],
                    'created_at': user[10].isoformat() if user[10] else None,
                    'updated_at': user[11].isoformat() if user[11] else None
                }
                for user in users
            ]
    
    def update_user_role(self, user_id, new_role):
        """Actualizar rol de usuario (solo admin)"""
        try:
            with get_conn() as conn:
                cursor = conn.cursor()
                # Verificar si el usuario existe
                user_exists = cursor.execute(
                    "SELECT id FROM users WHERE id = %s",
                    (user_id,)
                ).fetchone()
                
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
                user_exists = cursor.execute(
                    "SELECT id FROM users WHERE id = %s",
                    (user_id,)
                ).fetchone()
                
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