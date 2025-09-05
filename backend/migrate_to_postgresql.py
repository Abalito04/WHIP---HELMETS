#!/usr/bin/env python3
"""
Script para migrar datos de SQLite a PostgreSQL
Ejecutar solo una vez después de configurar PostgreSQL en Railway
"""

import sqlite3
import json
import os
import sys

# Agregar el directorio backend al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DATABASE_URL, FORCE_POSTGRESQL
from database import get_connection_string

def migrate_sqlite_to_postgresql():
    """Migra datos de SQLite a PostgreSQL"""
    
    print("🔄 Iniciando migración de SQLite a PostgreSQL...")
    
    # Verificar que PostgreSQL esté configurado
    if not DATABASE_URL and not FORCE_POSTGRESQL:
        print("❌ PostgreSQL no está configurado. Configura las variables de entorno primero.")
        return False
    
    try:
        # Conectar a PostgreSQL
        import psycopg2
        conn_pg = psycopg2.connect(get_connection_string())
        cursor_pg = conn_pg.cursor()
        print("✅ Conectado a PostgreSQL")
        
        # Conectar a SQLite
        conn_sqlite = sqlite3.connect('productos.db')
        conn_sqlite.row_factory = sqlite3.Row
        cursor_sqlite = conn_sqlite.cursor()
        print("✅ Conectado a SQLite")
        
        # Migrar productos
        print("📦 Migrando productos...")
        cursor_sqlite.execute("SELECT * FROM productos")
        productos = cursor_sqlite.fetchall()
        
        for producto in productos:
            try:
                # Convertir a diccionario
                producto_dict = dict(producto)
                
                # Insertar en PostgreSQL
                cursor_pg.execute("""
                    INSERT INTO productos (name, brand, price, category, sizes, stock, image, images, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        brand = EXCLUDED.brand,
                        price = EXCLUDED.price,
                        category = EXCLUDED.category,
                        sizes = EXCLUDED.sizes,
                        stock = EXCLUDED.stock,
                        image = EXCLUDED.image,
                        images = EXCLUDED.images,
                        status = EXCLUDED.status
                """, (
                    producto_dict['name'],
                    producto_dict['brand'],
                    producto_dict['price'],
                    producto_dict['category'],
                    producto_dict['sizes'],
                    producto_dict['stock'],
                    producto_dict['image'],
                    producto_dict['images'],
                    producto_dict['status']
                ))
                print(f"  ✅ Producto migrado: {producto_dict['name']}")
                
            except Exception as e:
                print(f"  ❌ Error migrando producto {producto_dict.get('name', 'Unknown')}: {e}")
        
        # Migrar usuarios
        print("👥 Migrando usuarios...")
        try:
            conn_users = sqlite3.connect('users.db')
            conn_users.row_factory = sqlite3.Row
            cursor_users = conn_users.cursor()
            
            cursor_users.execute("SELECT * FROM users")
            usuarios = cursor_users.fetchall()
            
            for usuario in usuarios:
                try:
                    usuario_dict = dict(usuario)
                    
                    cursor_pg.execute("""
                        INSERT INTO users (email, password_hash, name, role, created_at, last_login)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (email) DO UPDATE SET
                            password_hash = EXCLUDED.password_hash,
                            name = EXCLUDED.name,
                            role = EXCLUDED.role,
                            last_login = EXCLUDED.last_login
                    """, (
                        usuario_dict['email'],
                        usuario_dict['password_hash'],
                        usuario_dict['name'],
                        usuario_dict['role'],
                        usuario_dict['created_at'],
                        usuario_dict['last_login']
                    ))
                    print(f"  ✅ Usuario migrado: {usuario_dict['email']}")
                    
                except Exception as e:
                    print(f"  ❌ Error migrando usuario {usuario_dict.get('email', 'Unknown')}: {e}")
            
            conn_users.close()
            
        except Exception as e:
            print(f"  ⚠️ No se pudo migrar usuarios: {e}")
        
        # Confirmar cambios
        conn_pg.commit()
        print("✅ Migración completada exitosamente!")
        
        # Cerrar conexiones
        conn_pg.close()
        conn_sqlite.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        return False

if __name__ == "__main__":
    success = migrate_sqlite_to_postgresql()
    if success:
        print("\n🎉 ¡Migración exitosa! Ahora puedes usar PostgreSQL en Railway.")
        print("💡 Recuerda configurar las variables de entorno en Railway:")
        print("   - FORCE_POSTGRESQL=true")
        print("   - DATABASE_URL=tu_url_de_postgresql")
        print("   - SECRET_KEY=tu_clave_secreta")
        print("   - CLOUDINARY_* (tus credenciales)")
    else:
        print("\n❌ La migración falló. Revisa los errores arriba.")
        sys.exit(1)
