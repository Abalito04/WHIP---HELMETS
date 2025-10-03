#!/usr/bin/env python3
"""
Script para configurar MercadoPago paso a paso
"""

import os
import sys

def print_header():
    print("=" * 60)
    print("CONFIGURACION DE MERCADOPAGO PARA WHIP HELMETS")
    print("=" * 60)
    print()

def print_step(step, title):
    print(f"PASO {step}: {title}")
    print("-" * 40)

def print_instructions():
    print_header()
    
    print_step(1, "CREAR CUENTA EN MERCADOPAGO")
    print("1. Ve a: https://www.mercadopago.com.ar/")
    print("2. Crea una cuenta de desarrollador")
    print("3. Completa la verificación de identidad")
    print("4. Accede al panel de desarrolladores")
    print()
    
    print_step(2, "OBTENER CREDENCIALES")
    print("1. En el panel de desarrolladores, ve a 'Credenciales'")
    print("2. Copia tu 'Access Token' (clave privada)")
    print("3. Copia tu 'Public Key' (clave pública)")
    print("4. IMPORTANTE: Usa las credenciales de TEST para desarrollo")
    print()
    
    print_step(3, "CONFIGURAR EN RAILWAY")
    print("1. Ve a tu proyecto en Railway")
    print("2. Ve a la pestaña 'Variables'")
    print("3. Agrega estas variables:")
    print()
    print("   MERCADOPAGO_ACCESS_TOKEN = tu_access_token_aqui")
    print("   MERCADOPAGO_PUBLIC_KEY = tu_public_key_aqui")
    print()
    
    print_step(4, "CONFIGURAR WEBHOOKS")
    print("1. En MercadoPago, ve a 'Webhooks'")
    print("2. Agrega esta URL:")
    print("   https://whip-helmets.up.railway.app/api/payment/webhook")
    print("3. Selecciona los eventos: 'payment' y 'merchant_order'")
    print()
    
    print_step(5, "PROBAR LA INTEGRACIÓN")
    print("1. Ve a tu tienda online")
    print("2. Agrega productos al carrito")
    print("3. Ve al checkout")
    print("4. Selecciona 'MercadoPago' como método de pago")
    print("5. Completa el pago de prueba")
    print()
    
    print("MERCADOPAGO CONFIGURADO!")
    print("=" * 60)

def check_current_config():
    print("VERIFICANDO CONFIGURACION ACTUAL...")
    print()
    
    # Verificar variables de entorno
    access_token = os.environ.get('MERCADOPAGO_ACCESS_TOKEN')
    public_key = os.environ.get('MERCADOPAGO_PUBLIC_KEY')
    
    if access_token:
        print("[OK] MERCADOPAGO_ACCESS_TOKEN: Configurado")
        print(f"   Token: {access_token[:10]}...{access_token[-10:]}")
    else:
        print("[ERROR] MERCADOPAGO_ACCESS_TOKEN: No configurado")
    
    if public_key:
        print("[OK] MERCADOPAGO_PUBLIC_KEY: Configurado")
        print(f"   Key: {public_key[:10]}...{public_key[-10:]}")
    else:
        print("[ERROR] MERCADOPAGO_PUBLIC_KEY: No configurado")
    
    print()
    
    if access_token and public_key:
        print("MercadoPago esta configurado correctamente!")
        return True
    else:
        print("MercadoPago necesita configuracion")
        return False

def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--check':
        check_current_config()
    else:
        print_instructions()
        
        # Verificar configuración actual
        print()
        if not check_current_config():
            print()
            print("SIGUE LOS PASOS ARRIBA PARA CONFIGURAR MERCADOPAGO")
            print("   Luego ejecuta: python setup_mercadopago.py --check")

if __name__ == "__main__":
    main()
