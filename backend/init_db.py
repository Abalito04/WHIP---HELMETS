# init_db.py
import sqlite3
import os

DB_PATH = "productos.db"

def init_database():
    # Eliminar la base de datos existente si hay alguna
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("Base de datos anterior eliminada")
    
    # Conectar a la base de datos (se creará automáticamente si no existe)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Crear la tabla de productos con el campo de stock
    cursor.execute('''
        CREATE TABLE productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            brand TEXT,
            price REAL NOT NULL DEFAULT 0,
            category TEXT,
            sizes TEXT,
            stock INTEGER DEFAULT 0,  -- Nuevo campo: cantidad en stock
            image TEXT,
            status TEXT
        )
    ''')
    
    # Insertar datos de ejemplo - TODOS los productos
    sample_products = [
        ("Casco FOX V3", "Fox", 895000, "Cascos", "S,M,L,XL", 15, "css img/Fox V3 lateral.png", "Activo"),
        ("Casco FOX V3 RS", "Fox", 950000, "Cascos", "S,M,L,XL", 8, "css img/Fox V3 RS MC lateral.png", "Activo"),
        ("Casco FOX V1", "Fox", 500000, "Cascos", "S,M,L,XL", 22, "css img/Fox V1 lateral.png", "Activo"),
        ("Casco FLY Racing F2", "Fly Racing", 450000, "Cascos", "S,M,L,XL", 12, "css img/Fly Racing F2 lateral.png", "Activo"),
        ("Casco Bell Moto-9 Flex", "Bell", 650000, "Cascos", "M,L", 5, "css img/Bell Moto-9 Flex lateral.png", "Activo"),
        ("Casco Bell Moto-9 Flex 2", "Bell", 700000, "Cascos", "S,M,L,XL", 7, "css img/Bell Moto-9 Flex 2.png", "Activo"),
        ("Casco Alpinestars SM5", "Alpinestars", 550000, "Cascos", "S,M,L,XL", 18, "css img/Alpinestars SM5 lateral.png", "Activo"),
        ("Casco Aircraft 2 Carbono", "Aircraft", 1200000, "Cascos", "S,M,L", 3, "css img/Aircraft 2 Carbono.png", "Activo"),
        ("Casco Bell MX-9 Mips", "Bell", 480000, "Cascos", "S,M,L,XL", 10, "css img/Bell MX-9 Mips.png", "Activo"),
        ("Casco FOX V1 Interfere", "Fox", 520000, "Cascos", "S,M,L,XL", 14, "css img/Fox V1 Interfere.png", "Activo"),
        ("Casco Troy Lee Design D4", "Troy Lee Design", 850000, "Cascos", "S,M,L", 6, "css img/Troy Lee Design D4 lateral.png", "Activo"),
        ("Casco FOX V3 Moth LE Copper", "Fox", 1000000, "Cascos", "S,M,L,XL", 2, "css img/Fox V3 Moth LE Copper.png", "Activo"),
        ("Casco FOX V1 MATTE", "Fox", 530000, "Cascos", "S,M,L,XL", 9, "css img/FOX V1 MATTE.png", "Activo"),
        ("Casco Alpinestars SM5 amarillo", "Alpinestars", 560000, "Cascos", "S,M,L", 11, "css img/Alpinestars SM5 amarillo lateral.png", "Activo"),
        ("Guantes CROSS", "Fox", 50000, "Accesorios", "S,M,L", 25, "css img/Guantes FOX.png", "Activo"),
        ("Antiparras CROSS", "Fox", 80000, "Accesorios", "Único", 30, "css img/antiparras 2.png", "Activo")
    ]
    
    cursor.executemany('''
        INSERT INTO productos (name, brand, price, category, sizes, stock, image, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', sample_products)
    
    # Guardar cambios y cerrar conexión
    conn.commit()
    conn.close()
    
    print(f"Base de datos creada en {DB_PATH}")
    print(f"{len(sample_products)} productos insertados")

if __name__ == "__main__":
    init_database()