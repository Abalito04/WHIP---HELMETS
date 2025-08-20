from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
from contextlib import closing

DB_PATH = "productos.db"

app = Flask(__name__)
CORS(app)

# ---------------------- Database helpers ----------------------
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

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
                stock INTEGER DEFAULT 0,  -- Nuevo campo: cantidad en stock
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
            
            conn.executemany(
                """
                INSERT INTO productos (name, brand, price, category, sizes, stock, image, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                sample_products
            )
            print(f"{len(sample_products)} productos de ejemplo insertados")
            
def row_to_dict(row: sqlite3.Row):
    d = dict(row)
    # sizes: CSV -> lista
    if d.get("sizes"):
        d["sizes"] = [s.strip() for s in d["sizes"].split(",") if s.strip()]
    else:
        d["sizes"] = []
    # price a 2 decimales
    try:
        d["price"] = float(d["price"])
    except Exception:
        d["price"] = 0.0
    # stock a entero
    try:
        d["stock"] = int(d["stock"])
    except Exception:
        d["stock"] = 0
    return d


# ---------------------- API ----------------------

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "message": "API running"}), 200


@app.route("/api/products", methods=["GET"])
def list_products():
    """
    Opcional: filtros por querystring
    ?q=texto&brand=Fox&category=Cascos&status=Activo&min_price=0&max_price=1000000
    """
    q = request.args.get("q", "").strip()
    brand = request.args.get("brand", "").strip()
    category = request.args.get("category", "").strip()
    status = request.args.get("status", "").strip()
    min_price = request.args.get("min_price", "").strip()
    max_price = request.args.get("max_price", "").strip()

    query = "SELECT * FROM productos WHERE 1=1"
    params = []

    if q:
        query += " AND (LOWER(name) LIKE ? OR LOWER(brand) LIKE ? OR LOWER(category) LIKE ?)"
        like = f"%{q.lower()}%"
        params.extend([like, like, like])

    if brand:
        query += " AND LOWER(brand) = ?"
        params.append(brand.lower())

    if category:
        query += " AND LOWER(category) = ?"
        params.append(category.lower())

    if status:
        query += " AND LOWER(status) = ?"
        params.append(status.lower())

    if min_price:
        query += " AND price >= ?"
        params.append(float(min_price))

    if max_price:
        query += " AND price <= ?"
        params.append(float(max_price))

    query += " ORDER BY id DESC"

    with closing(get_conn()) as conn:
        rows = conn.execute(query, params).fetchall()
    return jsonify([row_to_dict(r) for r in rows]), 200


@app.route("/api/products/<int:pid>", methods=["GET"])
def get_product(pid: int):
    with closing(get_conn()) as conn:
        row = conn.execute("SELECT * FROM productos WHERE id = ?", (pid,)).fetchone()
        if not row:
            return jsonify({"error": "Producto no encontrado"}), 404
        return jsonify(row_to_dict(row)), 200


@app.route("/api/products", methods=["POST"])
def create_product():
    data = request.get_json(force=True) or {}

    # Validaciones mínimas
    name = (data.get("name") or "").strip()
    price = data.get("price", 0)
    if not name:
        return jsonify({"error": "El campo 'name' es obligatorio"}), 400
    try:
        price = float(price)
    except Exception:
        return jsonify({"error": "El campo 'price' debe ser numérico"}), 400

    brand = (data.get("brand") or "").strip()
    category = (data.get("category") or "").strip()
    sizes_list = data.get("sizes") or []
    if isinstance(sizes_list, str):
        # Permitimos recibir CSV también
        sizes_list = [s.strip() for s in sizes_list.split(",") if s.strip()]
    sizes_csv = ",".join(sizes_list)
    stock = data.get("stock", 0)
    try:
        stock = int(stock)
    except Exception:
        stock = 0
    image = (data.get("image") or "").strip()
    status = (data.get("status") or "Activo").strip() or "Activo"

    with closing(get_conn()) as conn, conn:
        cur = conn.execute(
            """
            INSERT INTO productos (name, brand, price, category, sizes, stock, image, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (name, brand, price, category, sizes_csv, stock, image, status),
        )
        new_id = cur.lastrowid

        row = conn.execute("SELECT * FROM productos WHERE id = ?", (new_id,)).fetchone()

    return jsonify(row_to_dict(row)), 201


@app.route("/api/products/<int:pid>", methods=["PUT", "PATCH"])
def update_product(pid: int):
    data = request.get_json(force=True) or {}

    fields = []
    params = []

    def set_field(key, value):
        fields.append(f"{key} = ?")
        params.append(value)

    # Campos opcionales
    if "name" in data:
        name = (data.get("name") or "").strip()
        if not name:
            return jsonify({"error": "El campo 'name' no puede estar vacío"}), 400
        set_field("name", name)

    if "brand" in data:
        set_field("brand", (data.get("brand") or "").strip())

    if "price" in data:
        try:
            price = float(data.get("price"))
        except Exception:
            return jsonify({"error": "El campo 'price' debe ser numérico"}), 400
        set_field("price", price)

    if "category" in data:
        set_field("category", (data.get("category") or "").strip())

    if "sizes" in data:
        sizes_list = data.get("sizes") or []
        if isinstance(sizes_list, str):
            sizes_list = [s.strip() for s in sizes_list.split(",") if s.strip()]
        set_field("sizes", ",".join(sizes_list))

    if "stock" in data:
        try:
            stock = int(data.get("stock"))
        except Exception:
            return jsonify({"error": "El campo 'stock' debe ser numérico"}), 400
        set_field("stock", stock)

    if "image" in data:
        set_field("image", (data.get("image") or "").strip())

    if "status" in data:
        set_field("status", (data.get("status") or "").strip())

    if not fields:
        return jsonify({"error": "Nada para actualizar"}), 400

    params.append(pid)

    with closing(get_conn()) as conn, conn:
        cur = conn.execute(f"UPDATE productos SET {', '.join(fields)} WHERE id = ?", params)
        if cur.rowcount == 0:
            return jsonify({"error": "Producto no encontrado"}), 404
        row = conn.execute("SELECT * FROM productos WHERE id = ?", (pid,)).fetchone()

    return jsonify(row_to_dict(row)), 200


@app.route("/api/products/<int:pid>", methods=["DELETE"])
def delete_product(pid: int):
    with closing(get_conn()) as conn, conn:
        cur = conn.execute("DELETE FROM productos WHERE id = ?", (pid,))
        if cur.rowcount == 0:
            return jsonify({"error": "Producto no encontrado"}), 404
    return jsonify({"ok": True}), 200


# ---------------------- Seed opcional ----------------------
@app.route("/api/seed", methods=["POST"])
def seed():
    """Inserta algunos productos de ejemplo (idempotente básica)."""
    sample = [
        {
            "name": "Casco FOX V3",
            "brand": "Fox",
            "price": 895000,
            "category": "Cascos",
            "sizes": ["S", "M", "L", "XL"],
            "stock": 15,
            "image": "css img/Fox V3 lateral.png",
            "status": "Activo",
        },
        {
            "name": "Casco Bell Moto-9 Flex",
            "brand": "Bell",
            "price": 650000,
            "category": "Cascos",
            "sizes": ["M", "L"],
            "stock": 5,
            "image": "css img/Bell Moto-9 Flex lateral.png",
            "status": "Activo",
        },
    ]
    with closing(get_conn()) as conn, conn:
        for p in sample:
            conn.execute(
                """
                INSERT INTO productos (name, brand, price, category, sizes, stock, image, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    p["name"],
                    p["brand"],
                    float(p["price"]),
                    p["category"],
                    ",".join(p["sizes"]),
                    p["stock"],
                    p["image"],
                    p["status"],
                ),
            )
    return jsonify({"ok": True, "inserted": len(sample)}), 201

# Añadir al server.py
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(force=True) or {}
    
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    
    # En un caso real, deberías verificar contra una base de datos
    # y usar hash para las contraseñas
    if username == "admin" and password == "admin":
        return jsonify({"success": True, "message": "Login exitoso"}), 200
    else:
        return jsonify({"success": False, "message": "Credenciales inválidas"}), 401


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=True)