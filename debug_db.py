#!/usr/bin/env python3
"""
Script para debuggear problemas de base de datos
"""

import sys
import os
sys.path.append('backend')

def test_database():
    """Prueba la conexión a la base de datos"""
    print("🔍 Debuggeando base de datos...")
    
    try:
        from config import FORCE_POSTGRESQL, DATABASE_URL
        print(f"FORCE_POSTGRESQL: {FORCE_POSTGRESQL}")
        print(f"DATABASE_URL: {DATABASE_URL}")
        
        if FORCE_POSTGRESQL or DATABASE_URL:
            print("Intentando conectar con PostgreSQL...")
            try:
                from database import get_conn as get_pg_conn
                with get_pg_conn() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    print("✅ PostgreSQL conectado")
            except Exception as e:
                print(f"❌ Error PostgreSQL: {e}")
                print("Cambiando a SQLite...")
        
        # Probar SQLite
        print("Probando SQLite...")
        import sqlite3
        conn = sqlite3.connect("productos.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT 1")
        print("✅ SQLite conectado")
        
        # Verificar si existe la tabla productos
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='productos'")
        if cursor.fetchone():
            print("✅ Tabla 'productos' existe")
            
            # Contar productos
            cursor = conn.execute("SELECT COUNT(*) FROM productos")
            count = cursor.fetchone()[0]
            print(f"✅ Productos en la base de datos: {count}")
            
            # Mostrar algunos productos
            cursor = conn.execute("SELECT id, name, brand FROM productos LIMIT 3")
            products = cursor.fetchall()
            for p in products:
                print(f"   - {p[0]}: {p[1]} ({p[2]})")
        else:
            print("❌ Tabla 'productos' no existe")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_database()
