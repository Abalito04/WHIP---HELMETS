from flask import Flask, request, jsonify, send_from_directory, g
from flask_cors import CORS
import sqlite3
import os
import re
from contextlib import closing
from database import get_conn, init_postgresql
from datetime import datetime, timedelta
import hashlib

# Importar el módulo de autenticación
try:
    from auth import auth_manager, require_auth, require_admin
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False
    print("⚠️  Módulo de autenticación no disponible")

# Procesamiento de imágenes deshabilitado
    IMAGE_PROCESSING_AVAILABLE = False

# Importar el manejador de pagos
try:
    from payment_handler import PaymentHandler
    payment_handler = PaymentHandler()
    PAYMENT_AVAILABLE = True
except ImportError:
    PAYMENT_AVAILABLE = False
    print("⚠️  Módulo de pagos no disponible")

# Importar configuración
from config import *

# Diccionario para almacenar intentos de login (rate limiting básico)
login_attempts = {}

def sanitize_input(text):
    """Sanitiza input del usuario"""
    if not text:
        return ""
    # Remover caracteres peligrosos
    text = re.sub(r'[<>"\']', '', str(text))
    return text.strip()

def check_rate_limit(ip, action, limit=5, window=300):
    """Verifica rate limiting básico"""
    now = datetime.now()
    key = f"{ip}_{action}"
    
    if key not in login_attempts:
        login_attempts[key] = []
    
    # Limpiar intentos antiguos
    login_attempts[key] = [t for t in login_attempts[key] if now - t < timedelta(seconds=window)]
    
    if len(login_attempts[key]) >= limit:
        return False
    
    login_attempts[key].append(now)
    return True

DB_PATH = "productos.db"

app = Flask(__name__)
CORS(app)

# ---------------------- Database helpers ----------------------
def get_conn():
    """Obtiene conexión a la base de datos (PostgreSQL o SQLite)"""
    from config import DATABASE_URL
    if DATABASE_URL:
        # Usar PostgreSQL
        from database import get_conn as get_pg_conn
        return get_pg_conn()
    else:
        # Usar SQLite
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def is_postgresql():
    """Verifica si estamos usando PostgreSQL"""
    from config import DATABASE_URL
    return bool(DATABASE_URL)

def get_placeholder():
    """Retorna el placeholder correcto para la base de datos actual"""
    return "%s" if is_postgresql() else "?"

def execute_query(conn, query, params=None):
    """Ejecuta una query con los placeholders correctos"""
    if params is None:
        return conn.execute(query)
    else:
        return conn.execute(query, params)

def init_db():
    """Inicializar todas las bases de datos"""
    print("Inicializando bases de datos...")
    
    # Verificar si tenemos PostgreSQL configurado
    from config import DATABASE_URL
    if DATABASE_URL:
        print("Usando PostgreSQL...")
        init_postgresql()
    else:
        print("Usando SQLite (desarrollo local)...")
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
                image TEXT,           -- URL o ruta de imagen principal
                images TEXT,          -- JSON array de URLs de imágenes adicionales
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
            
            placeholder = get_placeholder()
            conn.executemany(
                f"""
                INSERT INTO productos (name, brand, price, category, sizes, stock, image, status)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
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
            placeholder = get_placeholder()
            execute_query(conn,
                f"INSERT INTO users (username, password_hash, role) VALUES ({placeholder}, {placeholder}, {placeholder})",
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
            execute_query(conn,
                f"INSERT INTO users (username, password_hash, role) VALUES ({placeholder}, {placeholder}, {placeholder})",
                ('usuario', password_hash, 'user')
            )
            print("Usuario normal creado: usuario / user123")
        
        conn.commit()
        print("Base de datos de usuarios inicializada")
            
def row_to_dict(row):
    """Convierte una fila de base de datos a diccionario (PostgreSQL o SQLite)"""
    if hasattr(row, 'keys'):  # PostgreSQL RealDictRow
    d = dict(row)
    else:  # SQLite Row
        d = dict(row)
    
    # sizes: CSV -> lista
    if d.get("sizes"):
        d["sizes"] = [s.strip() for s in d["sizes"].split(",") if s.strip()]
    else:
        d["sizes"] = []
    
    # images: JSON string -> lista
    if d.get("images"):
        try:
            import json
            d["images"] = json.loads(d["images"])
        except Exception:
            d["images"] = []
    else:
        d["images"] = []
    
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
        placeholder = get_placeholder()
        row = execute_query(conn, f"SELECT * FROM productos WHERE id = {placeholder}", (pid,)).fetchone()
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
    
    # Manejar múltiples imágenes
    images_list = data.get("images") or []
    if isinstance(images_list, str):
        # Si viene como string, intentar parsear como JSON
        try:
            import json
            images_list = json.loads(images_list)
        except Exception:
            images_list = [images_list] if images_list else []
    elif not isinstance(images_list, list):
        images_list = []
    
    # Convertir a JSON string para almacenar en la base de datos
    import json
    images_json = json.dumps(images_list)
    
    status = (data.get("status") or "Activo").strip() or "Activo"

    with closing(get_conn()) as conn, conn:
        placeholder = get_placeholder()
        cur = execute_query(conn,
            f"""
            INSERT INTO productos (name, brand, price, category, sizes, stock, image, images, status)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            """,
            (name, brand, price, category, sizes_csv, stock, image, images_json, status),
        )
        new_id = cur.lastrowid if not is_postgresql() else cur.fetchone()[0] if hasattr(cur, 'fetchone') else None

        row = execute_query(conn, f"SELECT * FROM productos WHERE id = {placeholder}", (new_id,)).fetchone()

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

    if "images" in data:
        images_list = data.get("images") or []
        if isinstance(images_list, str):
            try:
                import json
                images_list = json.loads(images_list)
            except Exception:
                images_list = [images_list] if images_list else []
        elif not isinstance(images_list, list):
            images_list = []
        
        import json
        images_json = json.dumps(images_list)
        set_field("images", images_json)

    if "status" in data:
        set_field("status", (data.get("status") or "").strip())

    if not fields:
        return jsonify({"error": "Nada para actualizar"}), 400

    params.append(pid)

    with closing(get_conn()) as conn, conn:
        placeholder = get_placeholder()
        cur = execute_query(conn, f"UPDATE productos SET {', '.join(fields)} WHERE id = {placeholder}", params)
        if cur.rowcount == 0:
            return jsonify({"error": "Producto no encontrado"}), 404
        row = execute_query(conn, f"SELECT * FROM productos WHERE id = {placeholder}", (pid,)).fetchone()

    return jsonify(row_to_dict(row)), 200


@app.route("/api/products/<int:pid>", methods=["DELETE"])
def delete_product(pid: int):
    with closing(get_conn()) as conn, conn:
        placeholder = get_placeholder()
        cur = execute_query(conn, f"DELETE FROM productos WHERE id = {placeholder}", (pid,))
        if cur.rowcount == 0:
            return jsonify({"error": "Producto no encontrado"}), 404
    return jsonify({"ok": True}), 200


@app.route("/api/products/<int:pid>/images", methods=["GET"])
def get_product_images(pid: int):
    """Obtener todas las imágenes de un producto"""
    with closing(get_conn()) as conn:
        placeholder = get_placeholder()
        row = execute_query(conn, f"SELECT image, images FROM productos WHERE id = {placeholder}", (pid,)).fetchone()
        if not row:
            return jsonify({"error": "Producto no encontrado"}), 404
        
        product_dict = row_to_dict(row)
        all_images = [product_dict["image"]] + product_dict["images"]
        # Filtrar imágenes vacías
        all_images = [img for img in all_images if img and img.strip()]
        
        return jsonify({"images": all_images}), 200


@app.route("/api/products/<int:pid>/images", methods=["POST"])
def add_product_images(pid: int):
    """Agregar nuevas imágenes a un producto"""
    try:
        if 'files' not in request.files:
            return jsonify({"error": "No se encontraron archivos"}), 400
        
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({"error": "No se seleccionaron archivos"}), 400
        
        uploaded_urls = []
        
        # Verificar configuración de Cloudinary
        if not CLOUDINARY_CLOUD_NAME or not CLOUDINARY_API_KEY or not CLOUDINARY_API_SECRET:
            return jsonify({"error": "Cloudinary no configurado"}), 500
        
        # Configurar Cloudinary
        import cloudinary
        import cloudinary.uploader
        
        cloudinary.config(
            cloud_name=CLOUDINARY_CLOUD_NAME,
            api_key=CLOUDINARY_API_KEY,
            api_secret=CLOUDINARY_API_SECRET
        )
        
        # Subir cada archivo
        for file in files:
            if file.filename == '':
                continue
                
            # Verificar que sea una imagen
            if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                continue
            
            try:
                # Subir imagen a Cloudinary
                result = cloudinary.uploader.upload(
                    file,
                    folder=f"whip-helmets/products/{pid}",  # Organizar por producto
                    public_id=None,
                    resource_type="image",
                    transformation=[
                        {"width": 800, "height": 800, "crop": "limit"},
                        {"quality": "auto"}
                    ]
                )
                
                uploaded_urls.append(result['secure_url'])
                
            except Exception as e:
                print(f"Error al subir imagen {file.filename}: {e}")
                continue
        
        if not uploaded_urls:
            return jsonify({"error": "No se pudieron subir las imágenes"}), 500
        
        # Actualizar el producto con las nuevas imágenes
        with closing(get_conn()) as conn:
            placeholder = get_placeholder()
            row = execute_query(conn, f"SELECT images FROM productos WHERE id = {placeholder}", (pid,)).fetchone()
            if not row:
                return jsonify({"error": "Producto no encontrado"}), 404
            
            # Obtener imágenes existentes
            existing_images = []
            if row[0]:
                try:
                    import json
                    existing_images = json.loads(row[0])
                except Exception:
                    existing_images = []
            
            # Agregar nuevas imágenes
            all_images = existing_images + uploaded_urls
            
            # Actualizar en la base de datos
            import json
            images_json = json.dumps(all_images)
            execute_query(conn, f"UPDATE productos SET images = {placeholder} WHERE id = {placeholder}", (images_json, pid))
            conn.commit()
        
        return jsonify({
            "success": True,
            "message": f"{len(uploaded_urls)} imágenes agregadas correctamente",
            "uploaded_urls": uploaded_urls,
            "total_images": len(all_images)
        }), 200
        
    except Exception as e:
        print(f"Error al agregar imágenes: {e}")
        return jsonify({"error": f"Error al agregar imágenes: {str(e)}"}), 500


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


# ---------------------- Optimización de imágenes deshabilitada ----------------------

# ---------------------- SUBIDA DE IMÁGENES ----------------------

@app.route("/api/upload", methods=["POST"])
def upload_image():
    """Endpoint para subir imágenes a Cloudinary"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No se encontró archivo"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No se seleccionó archivo"}), 400
        
        # Verificar que sea una imagen
        if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
            return jsonify({"error": "Solo se permiten archivos de imagen"}), 400
        
        # Verificar configuración de Cloudinary
        if not CLOUDINARY_CLOUD_NAME or not CLOUDINARY_API_KEY or not CLOUDINARY_API_SECRET:
            # Modo temporal: guardar en local y devolver URL relativa
            import uuid
            import os
            
            # Crear directorio si no existe
            upload_dir = "../assets/images/products/uploaded"
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generar nombre único
            file_extension = file.filename.split('.')[-1]
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            file_path = os.path.join(upload_dir, unique_filename)
            
            # Guardar archivo
            file.save(file_path)
            
            # Devolver URL relativa
            relative_path = f"assets/images/products/uploaded/{unique_filename}"
            
            return jsonify({
                "success": True,
                "message": "Imagen subida correctamente (modo temporal)",
                "file_path": relative_path,
                "filename": file.filename,
                "note": "Cloudinary no configurado - usando almacenamiento temporal"
            }), 200
        
        # Configurar Cloudinary
        import cloudinary
        import cloudinary.uploader
        
        cloudinary.config(
            cloud_name=CLOUDINARY_CLOUD_NAME,
            api_key=CLOUDINARY_API_KEY,
            api_secret=CLOUDINARY_API_SECRET
        )
        
        # Subir imagen a Cloudinary
        result = cloudinary.uploader.upload(
            file,
            folder="whip-helmets/products",  # Organizar en carpeta
            public_id=None,  # Cloudinary genera ID único automáticamente
            resource_type="image",
            transformation=[
                {"width": 800, "height": 800, "crop": "limit"},  # Redimensionar si es muy grande
                {"quality": "auto"}  # Optimizar calidad automáticamente
            ]
        )
        
        # Retornar la URL de Cloudinary
        cloudinary_url = result['secure_url']
        
        return jsonify({
            "success": True,
            "message": "Imagen subida correctamente a Cloudinary",
            "file_path": cloudinary_url,
            "cloudinary_id": result['public_id'],
            "filename": file.filename
        }), 200
        
    except Exception as e:
        print(f"Error al subir imagen a Cloudinary: {e}")
        return jsonify({"error": f"Error al subir imagen: {str(e)}"}), 500


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
    """Endpoint para login de usuarios con rate limiting"""
    if not AUTH_AVAILABLE:
        return jsonify({"error": "Sistema de autenticación no disponible"}), 503
    
    try:
        # Rate limiting básico
        client_ip = request.remote_addr
        if not check_rate_limit(client_ip, 'login', limit=5, window=300):
            return jsonify({"error": "Demasiados intentos de login. Intenta en 5 minutos."}), 429
        
        data = request.get_json()
        username = sanitize_input(data.get('username', ''))
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({"error": "Usuario y contraseña requeridos"}), 400
        
        # Validar longitud mínima
        if len(username) < 3 or len(password) < 6:
            return jsonify({"error": "Usuario y contraseña deben tener al menos 3 y 6 caracteres respectivamente"}), 400
        
        result = auth_manager.login(username, password)
        return jsonify(result), 200 if result['success'] else 401
        
    except Exception as e:
        return jsonify({"error": "Error interno del servidor"}), 500

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
    
    # Configuración para Railway
    import os
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    app.run(host="0.0.0.0", port=port, debug=debug)