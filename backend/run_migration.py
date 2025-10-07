#!/usr/bin/env python3
"""
Script para ejecutar la migración de password_reset_tokens
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor

def run_migration():
    """Ejecutar migración de password_reset_tokens"""
    
    # Obtener configuración de la base de datos
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("ERROR: DATABASE_URL no encontrada en variables de entorno")
        return False
    
    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        print("OK: Conectado a la base de datos")
        
        # Leer el archivo SQL
        with open('migrate_password_reset.sql', 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Ejecutar la migración
        cursor.execute(sql_content)
        conn.commit()
        
        print("OK: Migración ejecutada exitosamente")
        
        # Verificar que la tabla se creó
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'password_reset_tokens'
        """)
        
        if cursor.fetchone():
            print("OK: Tabla 'password_reset_tokens' creada correctamente")
        else:
            print("ERROR: Tabla no se creó")
            return False
        
        # Verificar estructura de la tabla
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'password_reset_tokens'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        print("Estructura de la tabla:")
        for col_name, col_type in columns:
            print(f"   - {col_name}: {col_type}")
        
        cursor.close()
        conn.close()
        
        print("OK: Migración completada exitosamente")
        return True
        
    except Exception as e:
        print(f"ERROR ejecutando migración: {e}")
        return False

if __name__ == "__main__":
    print("Ejecutando migración de password_reset_tokens...")
    success = run_migration()
    
    if success:
        print("\nOK: Migración completada! El sistema de recuperación de contraseña está listo.")
    else:
        print("\nERROR: Error en la migración. Revisa los logs.")
