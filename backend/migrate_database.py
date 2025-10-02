#!/usr/bin/env python3
"""
Script de migración para crear las tablas necesarias para el sistema de pedidos
"""

import os
import sys
from database import get_conn

def create_orders_table():
    """Crear tabla orders si no existe"""
    try:
        with get_conn() as conn:
            cursor = conn.cursor()
            
            # Verificar si la tabla orders existe
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'orders'
            """)
            
            if not cursor.fetchone():
                print("Creando tabla orders...")
                cursor.execute("""
                    CREATE TABLE orders (
                        id SERIAL PRIMARY KEY,
                        order_number VARCHAR(50) UNIQUE NOT NULL,
                        customer_name VARCHAR(255) NOT NULL,
                        customer_email VARCHAR(255) NOT NULL,
                        customer_phone VARCHAR(50),
                        customer_address TEXT,
                        customer_city VARCHAR(100),
                        customer_zip VARCHAR(10),
                        total_amount DECIMAL(10,2) NOT NULL,
                        payment_method VARCHAR(50) DEFAULT 'mercadopago',
                        payment_id VARCHAR(255),
                        status VARCHAR(50) DEFAULT 'pending',
                        user_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                print("Tabla orders creada exitosamente")
            else:
                print("Tabla orders ya existe")
                
            # Verificar si las columnas necesarias existen
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'orders' AND column_name IN ('payment_method', 'customer_address', 'customer_city', 'customer_zip', 'user_id')
            """)
            existing_columns = [row[0] for row in cursor.fetchall()]
            
            # Agregar columnas faltantes
            if 'payment_method' not in existing_columns:
                print("Agregando columna payment_method...")
                cursor.execute("ALTER TABLE orders ADD COLUMN payment_method VARCHAR(50) DEFAULT 'mercadopago'")
                
            if 'customer_address' not in existing_columns:
                print("Agregando columna customer_address...")
                cursor.execute("ALTER TABLE orders ADD COLUMN customer_address TEXT")
                
            if 'customer_city' not in existing_columns:
                print("Agregando columna customer_city...")
                cursor.execute("ALTER TABLE orders ADD COLUMN customer_city VARCHAR(100)")
                
            if 'customer_zip' not in existing_columns:
                print("Agregando columna customer_zip...")
                cursor.execute("ALTER TABLE orders ADD COLUMN customer_zip VARCHAR(10)")
                
            if 'user_id' not in existing_columns:
                print("Agregando columna user_id...")
                cursor.execute("ALTER TABLE orders ADD COLUMN user_id INTEGER")
                
            if 'verification_code' not in existing_columns:
                print("Agregando columna verification_code...")
                cursor.execute("ALTER TABLE orders ADD COLUMN verification_code VARCHAR(20)")
            
            conn.commit()
            print("Columnas de orders verificadas")
            
    except Exception as e:
        print(f"Error creando tabla orders: {e}")
        raise

def create_order_items_table():
    """Crear tabla order_items si no existe"""
    try:
        with get_conn() as conn:
            cursor = conn.cursor()
            
            # Verificar si la tabla order_items existe
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'order_items'
            """)
            
            if not cursor.fetchone():
                print("Creando tabla order_items...")
                cursor.execute("""
                    CREATE TABLE order_items (
                        id SERIAL PRIMARY KEY,
                        order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                        product_id INTEGER NOT NULL,
                        quantity INTEGER NOT NULL DEFAULT 1,
                        price DECIMAL(10,2) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                print("Tabla order_items creada exitosamente")
            else:
                print("Tabla order_items ya existe")
                
            conn.commit()
            
    except Exception as e:
        print(f"Error creando tabla order_items: {e}")
        raise


def add_verification_code_column():
    """Agregar columna verification_code a la tabla orders si no existe"""
    try:
        with get_conn() as conn:
            cursor = conn.cursor()
            
            # Verificar si la columna verification_code existe
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'orders' AND column_name = 'verification_code'
            """)
            
            if not cursor.fetchone():
                print("Agregando columna verification_code a orders...")
                cursor.execute("ALTER TABLE orders ADD COLUMN verification_code VARCHAR(20)")
                
                # Generar códigos de verificación para pedidos existentes
                cursor.execute("""
                    UPDATE orders 
                    SET verification_code = UPPER(SUBSTRING(MD5(order_number || EXTRACT(EPOCH FROM created_at)::text), 1, 8))
                    WHERE verification_code IS NULL
                """)
                
                conn.commit()
                print("Columna verification_code agregada exitosamente")
            else:
                print("Columna verification_code ya existe")
                
    except Exception as e:
        print(f"Error agregando columna verification_code: {e}")
        raise

def main():
    """Ejecutar migración completa"""
    try:
        print("Iniciando migración de base de datos...")
        
        create_orders_table()
        create_order_items_table()
        add_verification_code_column()
        
        print("Migración completada exitosamente")
        
    except Exception as e:
        print(f"Error en migración: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
