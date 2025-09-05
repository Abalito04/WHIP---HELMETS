#!/usr/bin/env python3
"""
Script para diagnosticar problemas de subida de imágenes
"""
import os
import sys
sys.path.insert(0, 'backend')

def check_cloudinary_config():
    """Verificar configuración de Cloudinary"""
    print("🔍 Verificando configuración de Cloudinary...")
    
    from config import CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET
    
    print(f"CLOUDINARY_CLOUD_NAME: {'✅ Configurado' if CLOUDINARY_CLOUD_NAME else '❌ No configurado'}")
    print(f"CLOUDINARY_API_KEY: {'✅ Configurado' if CLOUDINARY_API_KEY else '❌ No configurado'}")
    print(f"CLOUDINARY_API_SECRET: {'✅ Configurado' if CLOUDINARY_API_SECRET else '❌ No configurado'}")
    
    if not all([CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET]):
        print("\n❌ PROBLEMA: Cloudinary no está completamente configurado")
        print("Variables de entorno faltantes:")
        if not CLOUDINARY_CLOUD_NAME:
            print("  - CLOUDINARY_CLOUD_NAME")
        if not CLOUDINARY_API_KEY:
            print("  - CLOUDINARY_API_KEY")
        if not CLOUDINARY_API_SECRET:
            print("  - CLOUDINARY_API_SECRET")
        return False
    else:
        print("\n✅ Cloudinary está configurado correctamente")
        return True

def test_cloudinary_connection():
    """Probar conexión con Cloudinary"""
    print("\n🔍 Probando conexión con Cloudinary...")
    
    try:
        import cloudinary
        from config import CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET
        
        cloudinary.config(
            cloud_name=CLOUDINARY_CLOUD_NAME,
            api_key=CLOUDINARY_API_KEY,
            api_secret=CLOUDINARY_API_SECRET
        )
        
        # Probar una operación simple
        import cloudinary.api
        result = cloudinary.api.ping()
        print("✅ Conexión con Cloudinary exitosa")
        return True
        
    except Exception as e:
        print(f"❌ Error al conectar con Cloudinary: {e}")
        return False

def check_upload_endpoint():
    """Verificar que el endpoint de upload esté disponible"""
    print("\n🔍 Verificando endpoint /api/upload...")
    
    try:
        import requests
        response = requests.get("https://web-production-4bac9.up.railway.app/api/upload", timeout=5)
        print(f"✅ Endpoint accesible (status: {response.status_code})")
        return True
    except Exception as e:
        print(f"❌ Error al acceder al endpoint: {e}")
        return False

if __name__ == "__main__":
    print("🚀 DIAGNÓSTICO DE SUBIDA DE IMÁGENES")
    print("=" * 50)
    
    config_ok = check_cloudinary_config()
    
    if config_ok:
        connection_ok = test_cloudinary_connection()
        endpoint_ok = check_upload_endpoint()
        
        if connection_ok and endpoint_ok:
            print("\n🎉 TODO FUNCIONA CORRECTAMENTE")
        else:
            print("\n⚠️  Hay problemas que resolver")
    else:
        print("\n❌ CONFIGURACIÓN REQUERIDA")
        print("Necesitas configurar las variables de entorno de Cloudinary en Railway")
