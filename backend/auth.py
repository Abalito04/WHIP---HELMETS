import sqlite3
import hashlib
import secrets
import time
from functools import wraps
from flask import request, jsonify, g

class AuthManager:
    def __init__(self, db_path='users.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Inicializar la base de datos de usuarios"""
        with sqlite3.connect(self.db_path) as conn:
            # Crear tabla si no existe
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user',
                    nombre TEXT,
                    apellido TEXT,
                    dni TEXT,
                    telefono TEXT,
                    direccion TEXT,
                    codigo_postal TEXT,
                    email TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Verificar si las nuevas columnas existen y agregarlas si no
            cursor = conn.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Lista de columnas que deberían existir
            required_columns = [
                ('nombre', 'TEXT'),
                ('apellido', 'TEXT'),
                ('dni', 'TEXT'),
                ('telefono', 'TEXT'),
                ('direccion', 'TEXT'),
                ('codigo_postal', 'TEXT'),
                ('email', 'TEXT'),
                ('updated_at', 'TIMESTAMP')
            ]
            
            # Agregar columnas faltantes
            for column_name, column_type in required_columns:
                if column_name not in columns:
                    try:
                        conn.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
                        print(f"Columna {column_name} agregada a la tabla users")
                    except Exception as e:
                        print(f"Error al agregar columna {column_name}: {e}")
            
            conn.commit()
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    token TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Crear usuario admin por defecto si no existe
            admin_exists = conn.execute(
                "SELECT id FROM users WHERE username = 'admin'"
            ).fetchone()
            
            if not admin_exists:
                password_hash = self.hash_password('admin123')
                conn.execute(
                    "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                    ('admin', password_hash, 'admin')
                )
            
            # Crear usuario normal por defecto si no existe
            user_exists = conn.execute(
                "SELECT id FROM users WHERE username = 'usuario'"
            ).fetchone()
            
            if not user_exists:
                password_hash = self.hash_password('user123')
                conn.execute(
                    "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                    ('usuario', password_hash, 'user')
                )
            
            conn.commit()
    
    def hash_password(self, password):
        """Hashear contraseña con SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password, password_hash):
        """Verificar contraseña"""
        return self.hash_password(password) == password_hash
    
    def create_session(self, user_id):
        """Crear una nueva sesión para el usuario"""
        token = secrets.token_urlsafe(32)
        expires_at = time.time() + (24 * 60 * 60)  # 24 horas
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, datetime(?, 'unixepoch'))",
                (user_id, token, expires_at)
            )
            conn.commit()
        
        return token
    
    def validate_session(self, token):
        """Validar token de sesión"""
        if not token:
            return None
        
        with sqlite3.connect(self.db_path) as conn:
            # Limpiar sesiones expiradas
            conn.execute("DELETE FROM sessions WHERE expires_at < datetime('now')")
            
            # Buscar sesión válida
            session = conn.execute(
                "SELECT s.user_id, u.username, u.role FROM sessions s "
                "JOIN users u ON s.user_id = u.id "
                "WHERE s.token = ? AND s.expires_at > datetime('now')",
                (token,)
            ).fetchone()
            
            conn.commit()
            
            if session:
                return {
                    'user_id': session[0],
                    'username': session[1],
                    'role': session[2]
                }
        
        return None
    
    def register(self, username, password, profile_data):
        """Registrar nuevo usuario"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Verificar si el usuario ya existe
                existing_user = conn.execute(
                    "SELECT id FROM users WHERE username = ?",
                    (username,)
                ).fetchone()
                
                if existing_user:
                    return {'success': False, 'error': 'El nombre de usuario ya existe'}
                
                # Verificar si el email ya existe (si se proporciona)
                if profile_data.get('email'):
                    existing_email = conn.execute(
                        "SELECT id FROM users WHERE email = ?",
                        (profile_data['email'],)
                    ).fetchone()
                    
                    if existing_email:
                        return {'success': False, 'error': 'El email ya está registrado'}
                
                # Crear hash de la contraseña
                password_hash = self.hash_password(password)
                
                # Verificar qué columnas existen
                cursor = conn.execute("PRAGMA table_info(users)")
                columns = [column[1] for column in cursor.fetchall()]
                
                # Mapear campos según la estructura de la base de datos
                field_mapping = {
                    'nombre': 'first_name' if 'first_name' in columns else 'nombre',
                    'apellido': 'last_name' if 'last_name' in columns else 'apellido',
                    'email': 'email',
                    'dni': 'dni' if 'dni' in columns else None,
                    'telefono': 'phone' if 'phone' in columns else 'telefono',
                    'direccion': 'address' if 'address' in columns else 'direccion',
                    'codigo_postal': 'postal_code' if 'postal_code' in columns else 'codigo_postal'
                }
                
                # Construir query de inserción dinámicamente
                insert_fields = ['username', 'password_hash', 'role']
                insert_values = [username, password_hash, 'user']
                
                for field, db_field in field_mapping.items():
                    if db_field and db_field in columns:
                        insert_fields.append(db_field)
                        insert_values.append(profile_data.get(field))
                
                placeholders = ', '.join(['?' for _ in insert_fields])
                query = f"INSERT INTO users ({', '.join(insert_fields)}) VALUES ({placeholders})"
                
                cursor = conn.execute(query, insert_values)
                
                user_id = cursor.lastrowid
                conn.commit()
                
                # Crear sesión automáticamente
                token = self.create_session(user_id)
                
                return {
                    'success': True,
                    'session_token': token,
                    'user': {
                        'id': user_id,
                        'username': username,
                        'role': 'user'
                    }
                }
                
        except Exception as e:
            return {'success': False, 'error': f'Error al registrar usuario: {str(e)}'}
    
    def login(self, username, password):
        """Autenticar usuario"""
        with sqlite3.connect(self.db_path) as conn:
            user = conn.execute(
                "SELECT id, username, password_hash, role FROM users WHERE username = ?",
                (username,)
            ).fetchone()
        
        if user and self.verify_password(password, user[2]):
            token = self.create_session(user[0])
            return {
                'success': True,
                'session_token': token,
                'user': {
                    'id': user[0],
                    'username': user[1],
                    'role': user[3]
                }
            }
        
        return {'success': False, 'error': 'Credenciales inválidas'}
    
    def logout(self, token):
        """Cerrar sesión"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()
        return {'success': True}
    
    def get_users(self):
        """Obtener lista de usuarios (solo admin)"""
        with sqlite3.connect(self.db_path) as conn:
            users = conn.execute(
                "SELECT id, username, role, created_at FROM users ORDER BY created_at DESC"
            ).fetchall()
        
        return [
            {
                'id': user[0],
                'username': user[1],
                'role': user[2],
                'created_at': user[3]
            }
            for user in users
        ]
    
    def get_user_by_id(self, user_id):
        """Obtener usuario por ID"""
        with sqlite3.connect(self.db_path) as conn:
            # Primero verificar qué columnas existen
            cursor = conn.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Construir query dinámicamente basado en las columnas existentes
            select_fields = ['id', 'username', 'role']
            
            # Mapear campos según la estructura de la base de datos
            field_mapping = {
                'nombre': 'first_name' if 'first_name' in columns else 'nombre',
                'apellido': 'last_name' if 'last_name' in columns else 'apellido',
                'email': 'email',
                'dni': 'dni' if 'dni' in columns else None,
                'telefono': 'phone' if 'phone' in columns else 'telefono',
                'direccion': 'address' if 'address' in columns else 'direccion',
                'codigo_postal': 'postal_code' if 'postal_code' in columns else 'codigo_postal'
            }
            
            for field, db_field in field_mapping.items():
                if db_field and db_field in columns:
                    select_fields.append(db_field)
            
            query = f"SELECT {', '.join(select_fields)} FROM users WHERE id = ?"
            user = conn.execute(query, (user_id,)).fetchone()
            
            if user:
                result = {
                    'id': user[0],
                    'username': user[1],
                    'role': user[2]
                }
                
                # Mapear los campos adicionales
                field_index = 3
                for field, db_field in field_mapping.items():
                    if db_field and db_field in columns and field_index < len(user):
                        result[field] = user[field_index]
                        field_index += 1
                    else:
                        result[field] = None
                
                return result
            return None
    
    def update_user_profile(self, user_id, profile_data):
        """Actualizar perfil de usuario"""
        with sqlite3.connect(self.db_path) as conn:
            # Verificar qué columnas existen
            cursor = conn.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Mapear campos según la estructura de la base de datos
            field_mapping = {
                'nombre': 'first_name' if 'first_name' in columns else 'nombre',
                'apellido': 'last_name' if 'last_name' in columns else 'apellido',
                'email': 'email',
                'dni': 'dni' if 'dni' in columns else None,
                'telefono': 'phone' if 'phone' in columns else 'telefono',
                'direccion': 'address' if 'address' in columns else 'direccion',
                'codigo_postal': 'postal_code' if 'postal_code' in columns else 'codigo_postal'
            }
            
            # Construir query de actualización dinámicamente
            update_fields = []
            update_values = []
            
            for field, db_field in field_mapping.items():
                if db_field and db_field in columns and field in profile_data:
                    update_fields.append(f"{db_field} = ?")
                    update_values.append(profile_data[field])
            
            if update_fields:
                update_values.append(user_id)
                query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
                conn.execute(query, update_values)
                conn.commit()
            
            return True

    def get_all_users(self):
        """Obtener todos los usuarios (para admin)"""
        with sqlite3.connect(self.db_path) as conn:
            users = conn.execute('''
                SELECT id, username, role, nombre, apellido, dni, telefono, 
                       direccion, codigo_postal, email, created_at
                FROM users
                ORDER BY created_at DESC
            ''').fetchall()
            
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
                    'created_at': user[10]
                }
                for user in users
            ]

    def update_user_by_admin(self, user_id, user_data):
        """Actualizar usuario por admin"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Verificar si el usuario existe
                user_exists = conn.execute(
                    "SELECT id FROM users WHERE id = ?", (user_id,)
                ).fetchone()
                
                if not user_exists:
                    return {'success': False, 'error': 'Usuario no encontrado'}
                
                # Verificar si el username ya existe (si se está cambiando)
                if user_data.get('username'):
                    existing_user = conn.execute(
                        "SELECT id FROM users WHERE username = ? AND id != ?", 
                        (user_data['username'], user_id)
                    ).fetchone()
                    if existing_user:
                        return {'success': False, 'error': 'El username ya está en uso'}
                
                # Verificar si el email ya existe (si se está cambiando)
                if user_data.get('email'):
                    existing_email = conn.execute(
                        "SELECT id FROM users WHERE email = ? AND id != ?", 
                        (user_data['email'], user_id)
                    ).fetchone()
                    if existing_email:
                        return {'success': False, 'error': 'El email ya está en uso'}
                
                # Construir query de actualización dinámicamente
                update_fields = []
                update_values = []
                
                for field in ['username', 'role', 'nombre', 'apellido', 'dni', 'telefono', 'direccion', 'codigo_postal', 'email']:
                    if field in user_data:
                        update_fields.append(f"{field} = ?")
                        update_values.append(user_data[field])
                
                if update_fields:
                    update_fields.append("updated_at = CURRENT_TIMESTAMP")
                    update_values.append(user_id)
                    
                    query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
                    conn.execute(query, update_values)
                    conn.commit()
                
                return {'success': True, 'message': 'Usuario actualizado correctamente'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def delete_user(self, user_id):
        """Eliminar usuario (solo admin)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Verificar si el usuario existe
                user_exists = conn.execute(
                    "SELECT id, role FROM users WHERE id = ?", (user_id,)
                ).fetchone()
                
                if not user_exists:
                    return {'success': False, 'error': 'Usuario no encontrado'}
                
                # No permitir eliminar al admin principal
                if user_exists[1] == 'admin' and user_id == 1:
                    return {'success': False, 'error': 'No se puede eliminar al administrador principal'}
                
                # Eliminar sesiones del usuario
                conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
                
                # Eliminar usuario
                conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
                conn.commit()
                
                return {'success': True, 'message': 'Usuario eliminado correctamente'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def create_user_by_admin(self, user_data):
        """Crear usuario por admin"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Verificar si el username ya existe
                existing_user = conn.execute(
                    "SELECT id FROM users WHERE username = ?", (user_data['username'],)
                ).fetchone()
                if existing_user:
                    return {'success': False, 'error': 'El username ya está en uso'}
                
                # Verificar si el email ya existe (si se proporciona)
                if user_data.get('email'):
                    existing_email = conn.execute(
                        "SELECT id FROM users WHERE email = ?", (user_data['email'],)
                    ).fetchone()
                    if existing_email:
                        return {'success': False, 'error': 'El email ya está en uso'}
                
                # Hash de la contraseña
                password_hash = self.hash_password(user_data['password'])
                
                # Insertar nuevo usuario
                conn.execute('''
                    INSERT INTO users (username, password_hash, role, nombre, apellido, 
                                     dni, telefono, direccion, codigo_postal, email)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_data['username'],
                    password_hash,
                    user_data.get('role', 'user'),
                    user_data.get('nombre'),
                    user_data.get('apellido'),
                    user_data.get('dni'),
                    user_data.get('telefono'),
                    user_data.get('direccion'),
                    user_data.get('codigo_postal'),
                    user_data.get('email')
                ))
                
                user_id = conn.lastrowid
                conn.commit()
                
                return {
                    'success': True, 
                    'message': 'Usuario creado correctamente',
                    'user_id': user_id
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

# Instancia global del AuthManager
auth_manager = AuthManager()

# Decoradores para proteger rutas
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token requerido'}), 401
        
        token = auth_header.split(' ')[1]
        user = auth_manager.validate_session(token)
        
        if not user:
            return jsonify({'error': 'Token inválido o expirado'}), 401
        
        g.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function

def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token requerido'}), 401
        
        token = auth_header.split(' ')[1]
        user = auth_manager.validate_session(token)
        
        if not user:
            return jsonify({'error': 'Token inválido o expirado'}), 401
        
        if user['role'] != 'admin':
            return jsonify({'error': 'Acceso denegado. Se requiere rol de administrador'}), 403
        
        g.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function
