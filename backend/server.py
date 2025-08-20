def init_db():
    print("Inicializando base de datos...")
    with closing(get_conn()) as conn, conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                brand TEXT,
                price REAL NOT NULL DEFAULT 0,
                category TEXT,
                sizes TEXT,           -- CSV ej: "S,M,L,XL"
                image TEXT,           -- URL o ruta de imagen
                status TEXT           -- ej: "Activo", "Agotado", "Oculto"
            );
            """
        )
        print("Tabla 'productos' creada o ya existente")
        
        # Verificar si la tabla está vacía y agregar datos de ejemplo
        cursor = conn.execute("SELECT COUNT(*) FROM productos")
        count = cursor.fetchone()[0]
        
        if count == 0:
            sample_products = [
                ("Casco FOX V3", "Fox", 895000, "Cascos", "S,M,L,XL", "css img/Fox V3 lateral.png", "Activo"),
                ("Casco FOX V3 RS", "Fox", 950000, "Cascos", "S,M,L,XL", "css img/Fox V3 RS MC lateral.png", "Activo"),
                ("Casco FOX V1", "Fox", 500000, "Cascos", "S,M,L,XL", "css img/Fox V1 lateral.png", "Activo"),
                ("Casco FLY Racing F2", "Fly Racing", 450000, "Cascos", "S,M,L,XL", "css img/Fly Racing F2 lateral.png", "Activo"),
                ("Casco Bell Moto-9 Flex", "Bell", 650000, "Cascos", "M,L", "css img/Bell Moto-9 Flex lateral.png", "Activo"),
                ("Casco Bell Moto-9 Flex 2", "Bell", 700000, "Cascos", "S,M,L,XL", "css img/Bell Moto-9 Flex 2.png", "Activo"),
                ("Casco Alpinestars SM5", "Alpinestars", 550000, "Cascos", "S,M,L,XL", "css img/Alpinestars SM5 lateral.png", "Activo"),
                ("Casco Aircraft 2 Carbono", "Aircraft", 1200000, "Cascos", "S,M,L", "css img/Aircraft 2 Carbono.png", "Activo"),
                ("Casco Bell MX-9 Mips", "Bell", 480000, "Cascos", "S,M,L,XL", "css img/Bell MX-9 Mips.png", "Activo"),
                ("Casco FOX V1 Interfere", "Fox", 520000, "Cascos", "S,M,L,XL", "css img/Fox V1 Interfere.png", "Activo"),
                ("Casco Troy Lee Design D4", "Troy Lee Design", 850000, "Cascos", "S,M,L", "css img/Troy Lee Design D4 lateral.png", "Activo"),
                ("Casco FOX V3 Moth LE Copper", "Fox", 1000000, "Cascos", "S,M,L,XL", "css img/Fox V3 Moth LE Copper.png", "Activo"),
                ("Casco FOX V1 MATTE", "Fox", 530000, "Cascos", "S,M,L,XL", "css img/FOX V1 MATTE.png", "Activo"),
                ("Casco Alpinestars SM5 amarillo", "Alpinestars", 560000, "Cascos", "S,M,L", "css img/Alpinestars SM5 amarillo lateral.png", "Activo"),
                ("Guantes CROSS", "Fox", 50000, "Accesorios", "S,M,L", "css img/Guantes FOX.png", "Activo"),
                ("Antiparras CROSS", "Fox", 80000, "Accesorios", "Único", "css img/antiparras 2.png", "Activo")
            ]
            
            conn.executemany(
                """
                INSERT INTO productos (name, brand, price, category, sizes, image, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                sample_products
            )
            print(f"{len(sample_products)} productos de ejemplo insertados")