#!/usr/bin/env python3
"""
Script para migrar la base de datos PostgreSQL y agregar el campo 'images'
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_conn

def migrate_add_images_column():
    """Agrega la columna 'images' a la tabla productos si no existe"""
    print("Migrando base de datos PostgreSQL...")
    
    try:
        with get_conn() as conn:
            cursor = conn.cursor()
            
            # Verificar si la columna 'images' ya existe
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'productos' AND column_name = 'images'
            """)
            
            if cursor.fetchone():
                print("La columna 'images' ya existe en la tabla productos")
            else:
                # Agregar la columna 'images'
                cursor.execute("""
                    ALTER TABLE productos 
                    ADD COLUMN images TEXT DEFAULT '[]'
                """)
                print("Columna 'images' agregada a la tabla productos")
            
            # Actualizar productos existentes que no tengan el campo images
            cursor.execute("""
                UPDATE productos 
                SET images = '[]' 
                WHERE images IS NULL OR images = ''
            """)
            
            conn.commit()
            print("Migración completada exitosamente")
            
    except Exception as e:
        print(f"Error durante la migración: {e}")
        raise e

if __name__ == "__main__":
    migrate_add_images_column()
