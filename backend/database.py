"""
Módulo para manejar conexiones a PostgreSQL
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from config import DATABASE_URL, PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD

def get_connection_string():
    """Obtiene la cadena de conexión a PostgreSQL"""
    if DATABASE_URL:
        return DATABASE_URL
    else:
        return f"host={PGHOST} port={PGPORT} dbname={PGDATABASE} user={PGUSER} password={PGPASSWORD}"

@contextmanager
def get_conn():
    """Context manager para conexiones a PostgreSQL"""
    conn = None
    try:
        conn = psycopg2.connect(get_connection_string())
        conn.autocommit = False
        yield conn
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

def init_postgresql_tables():
    """Inicializa las tablas en PostgreSQL"""
    print("Inicializando tablas de PostgreSQL...")
    
    with get_conn() as conn:
        cursor = conn.cursor()
        
        # Crear tabla de productos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                brand VARCHAR(100),
                price DECIMAL(10,2) NOT NULL DEFAULT 0,
                category VARCHAR(100),
                sizes TEXT,
                stock INTEGER DEFAULT 0,
                image TEXT,
                status VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Crear tabla de usuarios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL DEFAULT 'user',
                nombre VARCHAR(100),
                apellido VARCHAR(100),
                dni VARCHAR(20),
                telefono VARCHAR(20),
                direccion TEXT,
                codigo_postal VARCHAR(10),
                email VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Crear tabla de sesiones
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                token VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
        
        # Crear tabla de órdenes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                order_number VARCHAR(50) UNIQUE NOT NULL,
                customer_name VARCHAR(255) NOT NULL,
                customer_email VARCHAR(255) NOT NULL,
                customer_phone VARCHAR(20),
                total_amount DECIMAL(10,2) NOT NULL,
                status VARCHAR(50) DEFAULT 'pending',
                payment_id VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Crear tabla de items de órdenes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id SERIAL PRIMARY KEY,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES productos (id)
            )
        """)
        
        conn.commit()
        print("Tablas de PostgreSQL creadas correctamente")

def insert_sample_products():
    """Inserta productos de ejemplo en PostgreSQL"""
    print("Insertando productos de ejemplo...")
    
    with get_conn() as conn:
        cursor = conn.cursor()
        
        # Verificar si ya hay productos
        cursor.execute("SELECT COUNT(*) FROM productos")
        count = cursor.fetchone()[0]
        
        if count == 0:
            sample_products = [
                ("Casco FOX V3", "Fox", 895000, "Cascos", "S,M,L,XL", 15, "assets/images/products/Fox V3 lateral.png", "Activo"),
                ("Casco FOX V3 RS", "Fox", 950000, "Cascos", "S,M,L,XL", 8, "assets/images/products/Fox V3 RS MC lateral.png", "Activo"),
                ("Casco FOX V1", "Fox", 500000, "Cascos", "S,M,L,XL", 22, "assets/images/products/Fox V1 lateral.png", "Activo"),
                ("Casco FLY Racing F2", "Fly Racing", 450000, "Cascos", "S,M,L,XL", 12, "assets/images/products/Fly Racing F2 lateral.png", "Activo"),
                ("Casco Bell Moto-9 Flex", "Bell", 650000, "Cascos", "M,L", 5, "assets/images/products/Bell Moto-9 Flex lateral.png", "Activo"),
                ("Casco Bell Moto-9 Flex 2", "Bell", 700000, "Cascos", "S,M,L,XL", 7, "assets/images/products/Bell Moto-9 Flex 2.png", "Activo"),
                ("Casco Alpinestars SM5", "Alpinestars", 550000, "Cascos", "S,M,L,XL", 18, "assets/images/products/Alpinestars SM5 lateral.png", "Activo"),
                ("Casco Aircraft 2 Carbono", "Aircraft", 1200000, "Cascos", "S,M,L", 3, "assets/images/products/Aircraft 2 Carbono.png", "Activo"),
                ("Casco Bell MX-9 Mips", "Bell", 480000, "Cascos", "S,M,L,XL", 10, "assets/images/products/Bell MX-9 Mips.png", "Activo"),
                ("Casco FOX V1 Interfere", "Fox", 520000, "Cascos", "S,M,L,XL", 14, "assets/images/products/Fox V1 Interfere.png", "Activo"),
                ("Casco Troy Lee Design D4", "Troy Lee Design", 850000, "Cascos", "S,M,L", 6, "assets/images/products/Troy Lee Design D4 lateral.png", "Activo"),
                ("Casco FOX V3 Moth LE Copper", "Fox", 1000000, "Cascos", "S,M,L,XL", 2, "assets/images/products/Fox V3 Moth LE Copper.png", "Activo"),
                ("Casco FOX V1 MATTE", "Fox", 530000, "Cascos", "S,M,L,XL", 9, "assets/images/products/FOX V1 MATTE.png", "Activo"),
                ("Casco Alpinestars SM5 amarillo", "Alpinestars", 560000, "Cascos", "S,M,L", 11, "assets/images/products/Alpinestars SM5 amarillo lateral.png", "Activo"),
                ("Guantes CROSS", "Fox", 50000, "Accesorios", "S,M,L", 25, "assets/images/products/Guantes FOX.png", "Activo"),
                ("Antiparras CROSS", "Fox", 80000, "Accesorios", "Único", 30, "assets/images/products/antiparras 2.png", "Activo")
            ]
            
            cursor.executemany(
                """
                INSERT INTO productos (name, brand, price, category, sizes, stock, image, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                sample_products
            )
            
            conn.commit()
            print(f"{len(sample_products)} productos insertados en PostgreSQL")
        else:
            print(f"Ya existen {count} productos en la base de datos")

def insert_sample_users():
    """Inserta usuarios de ejemplo en PostgreSQL"""
    print("Insertando usuarios de ejemplo...")
    
    with get_conn() as conn:
        cursor = conn.cursor()
        
        # Verificar si ya hay usuarios
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        
        if count == 0:
            import hashlib
            
            # Usuario admin
            admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                ('admin', admin_password, 'admin')
            )
            
            # Usuario normal
            user_password = hashlib.sha256('user123'.encode()).hexdigest()
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                ('usuario', user_password, 'user')
            )
            
            conn.commit()
            print("Usuarios de ejemplo insertados: admin/admin123, usuario/user123")
        else:
            print(f"Ya existen {count} usuarios en la base de datos")

def init_postgresql():
    """Inicializa completamente PostgreSQL"""
    try:
        init_postgresql_tables()
        insert_sample_products()
        insert_sample_users()
        print("PostgreSQL inicializado correctamente")
    except Exception as e:
        print(f"Error al inicializar PostgreSQL: {e}")
        raise e
