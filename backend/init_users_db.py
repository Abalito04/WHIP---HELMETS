#!/usr/bin/env python3
"""
Script para inicializar la base de datos de usuarios
"""

import sqlite3
import hashlib
import os

def hash_password(password):
    """Hashear contraseña con SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_users_database():
    """Inicializar la base de datos de usuarios"""
    db_path = 'users.db'
    
    # Eliminar la base de datos existente si existe
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Base de datos existente eliminada: {db_path}")
    
    with sqlite3.connect(db_path) as conn:
        # Crear tabla de usuarios
        conn.execute('''
            CREATE TABLE users (
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
        
        # Crear tabla de sesiones
        conn.execute('''
            CREATE TABLE sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Crear usuario admin por defecto
        admin_password_hash = hash_password('admin123')
        conn.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            ('admin', admin_password_hash, 'admin')
        )
        
        # Crear usuario normal por defecto
        user_password_hash = hash_password('user123')
        conn.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            ('usuario', user_password_hash, 'user')
        )
        
        conn.commit()
        
        print(f"Base de datos de usuarios creada: {db_path}")
        print("Usuarios creados:")
        print("- admin / admin123 (rol: admin)")
        print("- usuario / user123 (rol: user)")

if __name__ == "__main__":
    init_users_database()
