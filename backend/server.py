from flask import Flask, request, jsonify, send_from_directory, g
from flask_cors import CORS
import sqlite3
import os
from contextlib import closing

# Importar el módulo de autenticación
try:
    from auth import auth_manager, require_auth, require_admin
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False
    print("⚠️  Módulo de autenticación no disponible")

# Importar el procesador de imágenes
try:
    from image_processor import image_processor
    IMAGE_PROCESSING_AVAILABLE = True
except ImportError:
    IMAGE_PROCESSING_AVAILABLE = False
    print("⚠️  Módulo de procesamiento de imágenes no disponible")

# Importar el manejador de pagos
try:
    from payment_handler import PaymentHandler
    payment_handler = PaymentHandler()
    PAYMENT_AVAILABLE = True
except ImportError:
    PAYMENT_AVAILABLE = False
    print("⚠️  Módulo de pagos no disponible")

DB_PATH = "productos.db"

app = Flask(__name__)
CORS(app)

# ---------------------- Database helpers ----------------------
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializar todas las bases de datos"""
    print("Inicializando bases de datos...")
    
    # Inicializar base de datos de productos
    init_products_db()
    
    # Inicializar base de datos de usuarios
    init_users_db()

def init_products_db():
    """Inicializar base de datos de productos"""
    print("Inicializando base de datos de productos...")
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
            
            conn.executemany(
                """
                INSERT INTO productos (name, brand, price, category, sizes, stock, image, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                sample_products
            )
            print(f"{len(sample_products)} productos de ejemplo insertados")

def init_users_db():
    """Inicializar base de datos de usuarios"""
    print("Inicializando base de datos de usuarios...")
    
    # Importar config para obtener la ruta de la base de datos de usuarios
    try:
        from config import USERS_DATABASE_PATH
        users_db_path = USERS_DATABASE_PATH
    except ImportError:
        users_db_path = "users.db"
    
    with sqlite3.connect(users_db_path) as conn:
        # Crear tabla de usuarios
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                nombre TEXT,
                apellido TEXT,
                dni TEXT,
                telefono TEXT,
                direccion TEXT,
                codigo_postal TEXT,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Crear tabla de sesiones
        conn.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Crear usuario admin por defecto si no existe
        admin_exists = conn.execute(
            "SELECT id FROM users WHERE username = 'admin'"
        ).fetchone()
        
        if not admin_exists:
            import hashlib
            password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
            conn.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                ('admin', password_hash, 'admin')
            )
            print("Usuario admin creado: admin / admin123")
        
        # Crear usuario normal por defecto si no existe
        user_exists = conn.execute(
            "SELECT id FROM users WHERE username = 'usuario'"
        ).fetchone()
        
        if not user_exists:
            import hashlib
            password_hash = hashlib.sha256('user123'.encode()).hexdigest()
            conn.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                ('usuario', password_hash, 'user')
            )
            print("Usuario normal creado: usuario / user123")
        
        conn.commit()
        print("Base de datos de usuarios inicializada")
            
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


# ---------------------- RUTAS PRINCIPALES ----------------------

@app.route("/")
def index():
    """Sirve la página principal"""
    return send_from_directory("..", "index.html")

@app.route("/<path:filename>")
def serve_static(filename):
    """Sirve archivos estáticos"""
    return send_from_directory("..", filename)

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
            "image": "assets/images/products/Fox V3 lateral.png",
            "status": "Activo",
        },
        {
            "name": "Casco Bell Moto-9 Flex",
            "brand": "Bell",
            "price": 650000,
            "category": "Cascos",
            "sizes": ["M", "L"],
            "stock": 5,
            "image": "assets/images/products/Bell Moto-9 Flex lateral.png",
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

# Esta ruta está duplicada y se elimina para evitar conflictos
# La ruta correcta es /api/auth/login


# ---------------------- Endpoints de optimización de imágenes ----------------------

@app.route("/api/images/optimize", methods=["POST"])
def optimize_images():
    """Optimiza automáticamente las imágenes nuevas"""
    if not IMAGE_PROCESSING_AVAILABLE:
        return jsonify({"error": "Procesamiento de imágenes no disponible"}), 503
    
    try:
        result = image_processor.process_new_images()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/images/stats", methods=["GET"])
def get_image_stats():
    """Obtiene estadísticas de optimización de imágenes"""
    if not IMAGE_PROCESSING_AVAILABLE:
        return jsonify({"error": "Procesamiento de imágenes no disponible"}), 503
    
    try:
        stats = image_processor.get_optimization_stats()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/images/cleanup", methods=["POST"])
def cleanup_images():
    """Limpia optimizaciones obsoletas"""
    if not IMAGE_PROCESSING_AVAILABLE:
        return jsonify({"error": "Procesamiento de imágenes no disponible"}), 503
    
    try:
        removed_count = image_processor.cleanup_old_optimizations()
        return jsonify({"removed": removed_count, "message": f"Eliminadas {removed_count} optimizaciones obsoletas"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------- Modificar endpoint de productos para optimización automática ----------------------

def optimize_product_image(image_path):
    """Optimiza la imagen de un producto si es necesario"""
    if not IMAGE_PROCESSING_AVAILABLE or not image_path:
        return image_path
    
    try:
        # Verificar si la imagen existe
        if not os.path.exists(image_path):
            return image_path
        
        # Obtener ruta optimizada
        optimized_path = image_processor.get_optimized_image_path(image_path, 'medium')
        
        # Si no existe la versión optimizada, procesarla
        if optimized_path == image_path:
            image_processor.optimize_single_image(image_path)
            optimized_path = image_processor.get_optimized_image_path(image_path, 'medium')
        
        return optimized_path
    except Exception as e:
        print(f"Error optimizando imagen {image_path}: {e}")
        return image_path

# Modificar la función row_to_dict para incluir optimización automática
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
    
    # Optimizar imagen automáticamente
    if d.get("image"):
        d["image"] = optimize_product_image(d["image"])
    
    return d

# ---------------------- RUTAS DE AUTENTICACIÓN ----------------------

@app.route("/api/auth/register", methods=["POST"])
def auth_register():
    """Endpoint para registro de nuevos usuarios"""
    if not AUTH_AVAILABLE:
        return jsonify({"error": "Sistema de autenticación no disponible"}), 503
    
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        profile_data = data.get('profile', {})
        
        # Validar campos requeridos
        if not username or not password:
            return jsonify({"error": "Usuario y contraseña son requeridos"}), 400
        
        # Validar longitud de contraseña
        if len(password) < 6:
            return jsonify({"error": "La contraseña debe tener al menos 6 caracteres"}), 400
        
        # Validar campos del perfil si se proporcionan
        required_fields = ['nombre', 'apellido', 'dni', 'telefono', 'email']
        for field in required_fields:
            if not profile_data.get(field):
                return jsonify({"error": f"Campo {field} es requerido"}), 400
        
        # Validar formato de email
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, profile_data['email']):
            return jsonify({"error": "Formato de email inválido"}), 400
        
        # Validar DNI (solo números)
        if not profile_data['dni'].isdigit():
            return jsonify({"error": "DNI debe contener solo números"}), 400
        
        # Validar código postal (opcional, pero si se proporciona debe ser numérico)
        if profile_data.get('codigo_postal') and not profile_data['codigo_postal'].isdigit():
            return jsonify({"error": "Código postal debe contener solo números"}), 400
        
        result = auth_manager.register(username, password, profile_data)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    """Endpoint para login de usuarios"""
    if not AUTH_AVAILABLE:
        return jsonify({"error": "Sistema de autenticación no disponible"}), 503
    
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"error": "Usuario y contraseña requeridos"}), 400
        
        result = auth_manager.login(username, password)
        return jsonify(result), 200 if result['success'] else 401
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/auth/logout", methods=["POST"])
@require_auth
def auth_logout():
    """Endpoint para logout de usuarios"""
    if not AUTH_AVAILABLE:
        return jsonify({"error": "Sistema de autenticación no disponible"}), 503
    
    try:
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(' ')[1]
        result = auth_manager.logout(token)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/auth/validate", methods=["GET"])
@require_auth
def auth_validate_session():
    """Validar sesión actual"""
    if not AUTH_AVAILABLE:
        return jsonify({"error": "Sistema de autenticación no disponible"}), 503
    
    try:
        return jsonify({
            "valid": True,
            "user": g.current_user
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/auth/users", methods=["GET"])
@require_admin
def auth_get_users():
    """Obtener lista de usuarios (solo admin)"""
    if not AUTH_AVAILABLE:
        return jsonify({"error": "Sistema de autenticación no disponible"}), 503
    
    try:
        users = auth_manager.get_users()
        return jsonify(users), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/profile", methods=["GET"])
@require_auth
def get_profile():
    """Obtener perfil del usuario autenticado"""
    if not AUTH_AVAILABLE:
        return jsonify({"error": "Sistema de autenticación no disponible"}), 503
    
    try:
        user = auth_manager.get_user_by_id(g.current_user['user_id'])
        if user:
            return jsonify(user), 200
        return jsonify({"error": "Usuario no encontrado"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/profile", methods=["PUT"])
@require_auth
def update_profile():
    """Actualizar perfil del usuario autenticado"""
    if not AUTH_AVAILABLE:
        return jsonify({"error": "Sistema de autenticación no disponible"}), 503
    
    try:
        data = request.get_json()
        
        # Validar campos requeridos
        required_fields = ['nombre', 'apellido', 'dni', 'telefono', 'email']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Campo {field} es requerido"}), 400
        
        # Validar formato de email
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data['email']):
            return jsonify({"error": "Formato de email inválido"}), 400
        
        # Validar DNI (solo números)
        if not data['dni'].isdigit():
            return jsonify({"error": "DNI debe contener solo números"}), 400
        
        # Validar código postal (opcional, pero si se proporciona debe ser numérico)
        if data.get('codigo_postal') and not data['codigo_postal'].isdigit():
            return jsonify({"error": "Código postal debe contener solo números"}), 400
        
        auth_manager.update_user_profile(g.current_user['user_id'], data)
        return jsonify({"success": True, "message": "Perfil actualizado correctamente"}), 200
        
    except Exception as e:
        return jsonify({"error": f"Error al actualizar perfil: {str(e)}"}), 500

# ---------------------- RUTA ADMIN PARA PRODUCTOS ----------------------

@app.route("/api/admin/products", methods=["GET"])
@require_admin
def list_products_admin():
    """Ruta para administradores - lista todos los productos sin filtros"""
    try:
        with closing(get_conn()) as conn:
            rows = conn.execute("SELECT * FROM productos ORDER BY id DESC").fetchall()
        return jsonify([row_to_dict(r) for r in rows]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------- RUTAS DE PAGOS ----------------------

@app.route("/api/payment/create-preference", methods=["POST"])
def create_payment_preference():
    """Crear preferencia de pago en MercadoPago"""
    if not PAYMENT_AVAILABLE:
        return jsonify({"error": "Sistema de pagos no disponible"}), 503
    
    # Verificar autenticación
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Token de autenticación requerido"}), 401
    
    token = auth_header.split(' ')[1]
    user = auth_manager.validate_session(token)
    if not user:
        return jsonify({"error": "Sesión inválida"}), 401
    
    try:
        data = request.get_json()
        items = data.get('items', [])
        customer_info = data.get('customer_info', {})
        
        if not items:
            return jsonify({"error": "Items requeridos"}), 400
        
        # Agregar información del usuario autenticado
        customer_info['user_id'] = user['user_id']
        customer_info['user_email'] = user.get('email', '')
        
        # Crear pedido en la base de datos
        total_amount = sum(item['price'] * item['quantity'] for item in items)
        order_result = payment_handler.create_order(items, customer_info, total_amount)
        
        if not order_result['success']:
            return jsonify(order_result), 500
        
        # Crear preferencia de pago
        preference_result = payment_handler.create_payment_preference(items, customer_info)
        
        if preference_result['success']:
            return jsonify({
                "success": True,
                "preference_id": preference_result['preference_id'],
                "init_point": preference_result['init_point'],
                "sandbox_init_point": preference_result['sandbox_init_point'],
                "order_number": order_result['order_number']
            }), 200
        else:
            return jsonify(preference_result), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/payment/webhook", methods=["POST"])
def payment_webhook():
    """Webhook para recibir notificaciones de MercadoPago"""
    if not PAYMENT_AVAILABLE:
        return jsonify({"error": "Sistema de pagos no disponible"}), 503
    
    try:
        data = request.get_json()
        result = payment_handler.process_webhook(data)
        
        if result['success']:
            return jsonify({"status": "ok"}), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/payment/status/<payment_id>", methods=["GET"])
def get_payment_status(payment_id):
    """Obtener estado de un pago"""
    if not PAYMENT_AVAILABLE:
        return jsonify({"error": "Sistema de pagos no disponible"}), 503
    
    try:
        result = payment_handler.get_payment_status(payment_id)
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/orders/<order_number>", methods=["GET"])
def get_order(order_number):
    """Obtener información de un pedido"""
    if not PAYMENT_AVAILABLE:
        return jsonify({"error": "Sistema de pagos no disponible"}), 503
    
    # Verificar autenticación
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Token de autenticación requerido"}), 401
    
    token = auth_header.split(' ')[1]
    user = auth_manager.validate_session(token)
    if not user:
        return jsonify({"error": "Sesión inválida"}), 401
    
    try:
        result = payment_handler.get_order(order_number, user['user_id'])
        return jsonify(result), 200 if result['success'] else 404
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/orders", methods=["GET"])
def get_user_orders():
    """Obtener todos los pedidos del usuario autenticado"""
    if not PAYMENT_AVAILABLE:
        return jsonify({"error": "Sistema de pagos no disponible"}), 503
    
    # Verificar autenticación
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Token de autenticación requerido"}), 401
    
    token = auth_header.split(' ')[1]
    user = auth_manager.validate_session(token)
    if not user:
        return jsonify({"error": "Sesión inválida"}), 401
    
    try:
        result = payment_handler.get_user_orders(user['user_id'])
        return jsonify(result), 200 if result['success'] else 404
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------- GESTIÓN DE USUARIOS (ADMIN) ----------------------

@app.route("/api/admin/users", methods=["GET"])
@require_admin
def get_all_users():
    """Obtener todos los usuarios (solo admin)"""
    try:
        users = auth_manager.get_all_users()
        return jsonify({"success": True, "users": users}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/admin/users/<int:user_id>", methods=["GET"])
@require_admin
def get_user(user_id):
    """Obtener un usuario específico (solo admin)"""
    try:
        user = auth_manager.get_user_by_id(user_id)
        if user:
            return jsonify({"success": True, "user": user}), 200
        else:
            return jsonify({"error": "Usuario no encontrado"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/admin/users/<int:user_id>", methods=["PUT"])
@require_admin
def update_user_admin(user_id):
    """Actualizar un usuario (solo admin)"""
    try:
        data = request.get_json()
        
        # Validaciones básicas
        if data.get('email') and not '@' in data['email']:
            return jsonify({"error": "Email inválido"}), 400
        
        if data.get('dni') and not data['dni'].isdigit():
            return jsonify({"error": "DNI debe contener solo números"}), 400
        
        if data.get('codigo_postal') and not data['codigo_postal'].isdigit():
            return jsonify({"error": "Código postal debe contener solo números"}), 400
        
        result = auth_manager.update_user_by_admin(user_id, data)
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/admin/users/<int:user_id>", methods=["DELETE"])
@require_admin
def delete_user(user_id):
    """Eliminar un usuario (solo admin)"""
    try:
        result = auth_manager.delete_user(user_id)
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/admin/users", methods=["POST"])
@require_admin
def create_user_admin():
    """Crear un nuevo usuario (solo admin)"""
    try:
        data = request.get_json()
        
        # Validaciones requeridas
        if not data.get('username') or not data.get('password'):
            return jsonify({"error": "Username y password son requeridos"}), 400
        
        if len(data['password']) < 6:
            return jsonify({"error": "La contraseña debe tener al menos 6 caracteres"}), 400
        
        if data.get('email') and not '@' in data['email']:
            return jsonify({"error": "Email inválido"}), 400
        
        if data.get('dni') and not data['dni'].isdigit():
            return jsonify({"error": "DNI debe contener solo números"}), 400
        
        if data.get('codigo_postal') and not data['codigo_postal'].isdigit():
            return jsonify({"error": "Código postal debe contener solo números"}), 400
        
        result = auth_manager.create_user_by_admin(data)
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------- RUTAS DE ARCHIVOS ESTÁTICOS ----------------------

@app.route("/assets/<path:filename>")
def serve_assets(filename):
    """Servir archivos estáticos desde assets/"""
    return send_from_directory("../assets", filename)

@app.route("/admin/<path:filename>")
def serve_admin(filename):
    """Servir archivos del admin"""
    return send_from_directory("../admin", filename)

@app.route("/pages/<path:filename>")
def serve_pages(filename):
    """Servir páginas estáticas"""
    return send_from_directory("../pages", filename)

@app.route("/payment/<path:filename>")
def serve_payment(filename):
    """Servir páginas de pago"""
    return send_from_directory("../payment", filename)

# ---------------------- RUTAS DE PÁGINAS DE PAGO ----------------------

@app.route("/payment/success")
def payment_success():
    """Página de pago exitoso"""
    return send_from_directory("payment", "success.html")

@app.route("/payment/failure")
def payment_failure():
    """Página de pago fallido"""
    return send_from_directory("payment", "failure.html")

@app.route("/payment/pending")
def payment_pending():
    """Página de pago pendiente"""
    return send_from_directory("payment", "pending.html")

if __name__ == "__main__":
    init_db()
    
    # Procesar imágenes nuevas al iniciar el servidor
    if IMAGE_PROCESSING_AVAILABLE:
        print("Procesando imagenes nuevas...")
        result = image_processor.process_new_images()
        print(f"OK: {result.get('message', 'Procesamiento completado')}")
    
    # Configuración para Railway
    import os
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    app.run(host="0.0.0.0", port=port, debug=debug)