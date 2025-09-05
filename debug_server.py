#!/usr/bin/env python3
"""
Script para debuggear el servidor Flask
"""

import sys
import os
sys.path.append('backend')

def test_server_functions():
    """Prueba las funciones del servidor"""
    print("🔍 Debuggeando funciones del servidor...")
    
    try:
        # Importar funciones del servidor
        from server import get_conn, execute_query, row_to_dict, get_placeholder
        from contextlib import closing
        
        print("✅ Funciones importadas correctamente")
        
        # Probar get_conn
        print("Probando get_conn()...")
        conn = get_conn()
        print(f"✅ get_conn() retornó: {type(conn)}")
        
        # Probar execute_query
        print("Probando execute_query()...")
        cursor = execute_query(conn, "SELECT COUNT(*) FROM productos")
        count = cursor.fetchone()[0]
        print(f"✅ execute_query() funcionó, productos: {count}")
        
        # Probar obtener productos
        print("Probando consulta de productos...")
        cursor = execute_query(conn, "SELECT * FROM productos LIMIT 1")
        row = cursor.fetchone()
        if row:
            print(f"✅ Producto obtenido: {row['name']}")
            
            # Probar row_to_dict
            print("Probando row_to_dict()...")
            product_dict = row_to_dict(row)
            print(f"✅ row_to_dict() funcionó: {product_dict['name']}")
        else:
            print("❌ No se encontraron productos")
        
        # Cerrar conexión
        conn.close()
        print("✅ Conexión cerrada")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_server_functions()
