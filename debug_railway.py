#!/usr/bin/env python3
"""
Script para diagnosticar la configuración de Railway
"""

import os
import sys

# Agregar el directorio backend al path
sys.path.append('backend')

def check_environment():
    """Verifica las variables de entorno"""
    print("🔍 Verificando variables de entorno...")
    
    # Variables importantes
    important_vars = [
        'DATABASE_URL',
        'FORCE_POSTGRESQL', 
        'PGHOST',
        'PGPORT',
        'PGDATABASE',
        'PGUSER',
        'PGPASSWORD',
        'SECRET_KEY',
        'CLOUDINARY_CLOUD_NAME',
        'RAILWAY_STATIC_URL',
        'RAILWAY_PUBLIC_DOMAIN'
    ]
    
    for var in important_vars:
        value = os.environ.get(var, 'NO CONFIGURADA')
        if var in ['PGPASSWORD', 'SECRET_KEY'] and value != 'NO CONFIGURADA':
            value = '***CONFIGURADA***'
        print(f"  {var}: {value}")
    
    print()

def check_database_config():
    """Verifica la configuración de la base de datos"""
    print("🗄️ Verificando configuración de base de datos...")
    
    try:
        from backend.config import DATABASE_URL, FORCE_POSTGRESQL, PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD
        
        print(f"  DATABASE_URL: {'CONFIGURADA' if DATABASE_URL else 'NO CONFIGURADA'}")
        print(f"  FORCE_POSTGRESQL: {FORCE_POSTGRESQL}")
        print(f"  PGHOST: {PGHOST}")
        print(f"  PGPORT: {PGPORT}")
        print(f"  PGDATABASE: {PGDATABASE}")
        print(f"  PGUSER: {PGUSER}")
        print(f"  PGPASSWORD: {'CONFIGURADA' if PGPASSWORD else 'NO CONFIGURADA'}")
        
        # Verificar si estamos en Railway
        is_railway = any(var in os.environ for var in ['RAILWAY_STATIC_URL', 'RAILWAY_PUBLIC_DOMAIN', 'RAILWAY_ENVIRONMENT'])
        print(f"  ¿Estamos en Railway?: {is_railway}")
        
    except Exception as e:
        print(f"  ❌ Error al importar configuración: {e}")
    
    print()

def test_postgresql_connection():
    """Prueba la conexión a PostgreSQL"""
    print("🔌 Probando conexión a PostgreSQL...")
    
    try:
        from backend.database import get_connection_string, get_conn
        
        connection_string = get_connection_string()
        print(f"  Cadena de conexión: {connection_string[:50]}...")
        
        with get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print(f"  ✅ Conexión exitosa: {result}")
            
            # Verificar tablas
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = cursor.fetchall()
            print(f"  📋 Tablas encontradas: {[t[0] for t in tables]}")
            
            # Verificar productos
            if 'productos' in [t[0] for t in tables]:
                cursor.execute("SELECT COUNT(*) FROM productos")
                count = cursor.fetchone()[0]
                print(f"  📦 Productos en la base de datos: {count}")
            
    except Exception as e:
        print(f"  ❌ Error de conexión: {e}")
    
    print()

def test_sqlite_fallback():
    """Prueba el fallback a SQLite"""
    print("💾 Probando fallback a SQLite...")
    
    try:
        import sqlite3
        
        # Verificar archivos SQLite
        sqlite_files = ['productos.db', 'users.db']
        for file in sqlite_files:
            if os.path.exists(file):
                conn = sqlite3.connect(file)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                print(f"  📁 {file}: {[t[0] for t in tables]}")
                conn.close()
            else:
                print(f"  📁 {file}: NO EXISTE")
                
    except Exception as e:
        print(f"  ❌ Error con SQLite: {e}")
    
    print()

if __name__ == "__main__":
    print("🚀 Diagnóstico de Railway - WHIP Helmets")
    print("=" * 50)
    
    check_environment()
    check_database_config()
    test_postgresql_connection()
    test_sqlite_fallback()
    
    print("✅ Diagnóstico completado")
