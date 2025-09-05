#!/usr/bin/env python3
"""
Script para probar la API y verificar que la base de datos funciona
"""

import requests
import json
import sys

def test_api():
    """Prueba la API local"""
    base_url = "http://127.0.0.1:5000"
    
    print("🧪 Probando API local...")
    
    # Probar endpoint de salud
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        print(f"✅ Health check: {response.status_code}")
        if response.status_code == 200:
            print(f"   Respuesta: {response.json()}")
    except Exception as e:
        print(f"❌ Error en health check: {e}")
        return False
    
    # Probar endpoint de productos
    try:
        response = requests.get(f"{base_url}/api/products", timeout=5)
        print(f"✅ Products endpoint: {response.status_code}")
        if response.status_code == 200:
            products = response.json()
            print(f"   Productos encontrados: {len(products)}")
            if products:
                print(f"   Primer producto: {products[0].get('name', 'N/A')}")
        else:
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error en products endpoint: {e}")
        return False
    
    # Probar endpoint de admin (sin autenticación)
    try:
        response = requests.get(f"{base_url}/api/admin/products", timeout=5)
        print(f"✅ Admin products endpoint: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Correctamente protegido (requiere autenticación)")
        else:
            print(f"   Respuesta: {response.text}")
    except Exception as e:
        print(f"❌ Error en admin endpoint: {e}")
    
    print("\n🎉 Pruebas completadas!")
    return True

if __name__ == "__main__":
    if test_api():
        print("✅ API funcionando correctamente")
        sys.exit(0)
    else:
        print("❌ API tiene problemas")
        sys.exit(1)
