#!/usr/bin/env python3
"""
Script de prueba para verificar que la API esté funcionando
"""
import requests
import json

def test_api():
    """Prueba la API de productos"""
    base_url = "https://web-production-4bac9.up.railway.app"
    
    print("🧪 Probando API de productos...")
    
    try:
        # Probar endpoint de salud
        print("1. Probando /api/health...")
        response = requests.get(f"{base_url}/api/health", timeout=10)
        if response.status_code == 200:
            print("✅ /api/health funciona")
        else:
            print(f"❌ /api/health falló: {response.status_code}")
            
        # Probar endpoint de productos
        print("2. Probando /api/products...")
        response = requests.get(f"{base_url}/api/products", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ /api/products funciona - {len(data)} productos encontrados")
            if data:
                print(f"   Primer producto: {data[0].get('name', 'N/A')}")
        else:
            print(f"❌ /api/products falló: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Timeout - El servidor está tardando mucho en responder")
    except requests.exceptions.ConnectionError:
        print("🔌 Error de conexión - El servidor no está disponible")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    test_api()
