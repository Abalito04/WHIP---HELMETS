#!/usr/bin/env python3
"""
Script para probar la conexión a la base de datos
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_sqlite():
    """Probar conexión a SQLite"""
    print("Probando SQLite...")
    try:
        import sqlite3
        conn = sqlite3.connect("productos.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT 1 as test")
        result = cursor.fetchone()
        print(f"✅ SQLite funciona: {result['test']}")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error con SQLite: {e}")
        return False

def test_postgresql():
    """Probar conexión a PostgreSQL"""
    print("Probando PostgreSQL...")
    try:
        from database import get_conn
        with get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            print(f"✅ PostgreSQL funciona: {result['test']}")
        return True
    except Exception as e:
        print(f"❌ Error con PostgreSQL: {e}")
        return False

if __name__ == "__main__":
    print("=== Prueba de conexiones a base de datos ===")
    
    # Probar PostgreSQL primero
    pg_ok = test_postgresql()
    
    # Probar SQLite
    sqlite_ok = test_sqlite()
    
    print("\n=== Resumen ===")
    if pg_ok:
        print("✅ Usar PostgreSQL")
    elif sqlite_ok:
        print("✅ Usar SQLite")
    else:
        print("❌ Ninguna base de datos funciona")
