#!/usr/bin/env python3
"""
Script simple para probar la API
"""

import sys
import os
sys.path.append('backend')

def test_simple():
    """Prueba simple de la API"""
    try:
        from server import app
        
        with app.test_client() as client:
            print("Probando health endpoint...")
            response = client.get('/api/health')
            print(f"Health: {response.status_code}")
            print(f"Response: {response.get_json()}")
            
            print("\nProbando products endpoint...")
            response = client.get('/api/products')
            print(f"Products: {response.status_code}")
            if response.status_code == 200:
                data = response.get_json()
                print(f"Products count: {len(data)}")
            else:
                print(f"Error: {response.get_data()}")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple()
