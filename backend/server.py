from flask import Flask, request, jsonify, send_from_directory, g
from flask_cors import CORS
import os
import re
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

app = Flask(__name__)
app.config['DEBUG'] = True
CORS(app)

# ---------------------- Database helpers ----------------------
def get_conn():
    """Obtiene conexión a PostgreSQL"""
    from database import get_connection_string
    import psycopg2
    conn = psycopg2.connect(get_connection_string())
    return conn

def execute_query(conn, query, params=None):
    """Ejecuta una query en PostgreSQL"""
    cursor = conn.cursor()
    if params is None:
        cursor.execute(query)
    else:
        cursor.execute(query, params)
    return cursor

def init_db():
    """Inicializar PostgreSQL"""
    print("Inicializando PostgreSQL...")
    
    try:
        # Verificar configuración de base de datos
        from config import check_database_config
        check_database_config()
        print("✅ Configuración de base de datos verificada")
        
        # Verificar conexión a PostgreSQL
        from database import get_conn as get_pg_conn
        with get_pg_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            print("✅ Conexión a PostgreSQL exitosa")
        
        # Inicializar PostgreSQL
        from database import init_postgresql
        init_postgresql()
        print("✅ PostgreSQL inicializado correctamente")
        
    except Exception as e:
        print(f"❌ Error al inicializar PostgreSQL: {e}")
        raise e

            
def row_to_dict(row):
    """Convierte una fila de PostgreSQL a diccionario"""
    # PostgreSQL - row es un RealDictRow
    if hasattr(row, '_asdict'):
        d = row._asdict()
    else:
        # Si no tiene _asdict, crear diccionario manualmente
        d = {}
        columns = ['id', 'name', 'brand', 'price', 'porcentaje_descuento', 'category', 'sizes', 'stock', 'image', 'images', 'status']
        for i, col in enumerate(columns):
            if i < len(row):
                d[col] = row[i]
    
    # sizes: CSV -> lista
    if d.get("sizes") and isinstance(d["sizes"], str):
        d["sizes"] = [s.strip() for s in d["sizes"].split(",") if s.strip()]
    else:
        d["sizes"] = []
    
    # images: JSON string -> lista
    if d.get("images") and isinstance(d["images"], str):
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
    
    # porcentaje_descuento a float (puede ser None)
    if d.get("porcentaje_descuento") is not None:
        try:
            d["porcentaje_descuento"] = float(d["porcentaje_descuento"])
            # Calcular precio_efectivo basado en el porcentaje
            if d["porcentaje_descuento"] > 0:
                descuento = d["price"] * (d["porcentaje_descuento"] / 100)
                d["precio_efectivo"] = round(d["price"] - descuento, 2)
            else:
                d["precio_efectivo"] = d["price"]
        except Exception:
            d["porcentaje_descuento"] = None
            d["precio_efectivo"] = d["price"]
    else:
        d["porcentaje_descuento"] = None
        d["precio_efectivo"] = d["price"]
    
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
    try:
        q = request.args.get("q", "").strip()
        brand = request.args.get("brand", "").strip()
        category = request.args.get("category", "").strip()
        status = request.args.get("status", "").strip()
        min_price = request.args.get("min_price", "").strip()
        max_price = request.args.get("max_price", "").strip()

        query = "SELECT id, name, brand, price, COALESCE(porcentaje_descuento, NULL) as porcentaje_descuento, category, sizes, stock, image, images, status, created_at, updated_at FROM productos WHERE 1=1"
        params = []

        if q:
            query += " AND (LOWER(name) LIKE %s OR LOWER(brand) LIKE %s OR LOWER(category) LIKE %s)"
            like = f"%{q.lower()}%"
            params.extend([like, like, like])

        if brand:
            query += " AND LOWER(brand) = %s"
            params.append(brand.lower())

        if category:
            query += " AND LOWER(category) = %s"
            params.append(category.lower())

        if status:
            query += " AND LOWER(status) = %s"
            params.append(status.lower())

        if min_price:
            query += " AND price >= %s"
            params.append(float(min_price))

        if max_price:
            query += " AND price <= %s"
            params.append(float(max_price))

        query += " ORDER BY id DESC"

        print(f"DEBUG: Query: {query}")
        print(f"DEBUG: Params: {params}")

        conn = get_conn()
        try:
            rows = execute_query(conn, query, params).fetchall()
            print(f"DEBUG: Rows found: {len(rows)}")
            result = [row_to_dict(r) for r in rows]
            print(f"DEBUG: Result length: {len(result)}")
            return jsonify(result), 200
        finally:
            conn.close()
        
    except Exception as e:
        print(f"ERROR in list_products: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/products/<int:pid>", methods=["GET"])
def get_product(pid: int):
    conn = get_conn()
    try:
        row = execute_query(conn, "SELECT id, name, brand, price, COALESCE(porcentaje_descuento, NULL) as porcentaje_descuento, category, sizes, stock, image, images, status, created_at, updated_at FROM productos WHERE id = %s", (pid,)).fetchone()
        if not row:
            return jsonify({"error": "Producto no encontrado"}), 404
        return jsonify(row_to_dict(row)), 200
    finally:
        conn.close()


@app.route("/api/products", methods=["POST"])
def create_product():
    data = request.get_json(force=True) or {}

    # Validaciones mínimas
    name = (data.get("name") or "").strip()
    price = data.get("price", 0)
    porcentaje_descuento = data.get("porcentaje_descuento")
    if not name:
        return jsonify({"error": "El campo 'name' es obligatorio"}), 400
    try:
        price = float(price)
    except Exception:
        return jsonify({"error": "El campo 'price' debe ser numérico"}), 400
    
    # Validar porcentaje_descuento si se proporciona
    if porcentaje_descuento is not None:
        try:
            porcentaje_descuento = float(porcentaje_descuento)
            if porcentaje_descuento < 0 or porcentaje_descuento > 100:
                return jsonify({"error": "El porcentaje de descuento debe estar entre 0 y 100"}), 400
        except Exception:
            return jsonify({"error": "El campo 'porcentaje_descuento' debe ser numérico"}), 400

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

    conn = get_conn()
    try:
        cur = execute_query(conn,
            """
            INSERT INTO productos (name, brand, price, porcentaje_descuento, category, sizes, stock, image, images, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (name, brand, price, porcentaje_descuento, category, sizes_csv, stock, image, images_json, status),
        )
        
        # PostgreSQL: obtener el ID del último insert
        new_id = cur.fetchone()[0]
        conn.commit()  # Confirmar la transacción

        row = execute_query(conn, "SELECT id, name, brand, price, COALESCE(porcentaje_descuento, NULL) as porcentaje_descuento, category, sizes, stock, image, images, status, created_at, updated_at FROM productos WHERE id = %s", (new_id,)).fetchone()
        return jsonify(row_to_dict(row)), 201
    finally:
        conn.close()


@app.route("/api/products/<int:pid>", methods=["PUT", "PATCH"])
def update_product(pid: int):
    try:
        data = request.get_json(force=True) or {}
        print(f"DEBUG: Actualizando producto {pid} con datos: {data}")

        fields = []
        params = []

        def set_field(key, value):
            fields.append(f"{key} = %s")
            params.append(value)
            print(f"DEBUG: Campo {key} = {value}")

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

        if "porcentaje_descuento" in data:
            porcentaje_descuento = data.get("porcentaje_descuento")
            if porcentaje_descuento is not None and porcentaje_descuento != "":
                try:
                    porcentaje_descuento = float(porcentaje_descuento)
                    if porcentaje_descuento < 0 or porcentaje_descuento > 100:
                        return jsonify({"error": "El porcentaje de descuento debe estar entre 0 y 100"}), 400
                except Exception:
                    return jsonify({"error": "El campo 'porcentaje_descuento' debe ser numérico"}), 400
            # Verificar si la columna existe antes de intentar actualizarla
            try:
                conn_check = get_conn()
                try:
                    cursor_check = conn_check.cursor()
                    cursor_check.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'productos' AND column_name = 'porcentaje_descuento'
                    """)
                    column_exists = cursor_check.fetchone() is not None
                    if column_exists:
                        set_field("porcentaje_descuento", porcentaje_descuento)
                    else:
                        print(f"WARNING: Columna porcentaje_descuento no existe, saltando actualización")
                finally:
                    conn_check.close()
            except Exception as e:
                print(f"WARNING: Error verificando columna porcentaje_descuento: {e}")
                # Si no podemos verificar, intentar de todas formas
                set_field("porcentaje_descuento", porcentaje_descuento)

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

        conn = get_conn()
        try:
            print(f"DEBUG: Query: UPDATE productos SET {', '.join(fields)} WHERE id = %s")
            print(f"DEBUG: Params: {params}")
            
            cur = execute_query(conn, f"UPDATE productos SET {', '.join(fields)} WHERE id = %s", params)
            if cur.rowcount == 0:
                return jsonify({"error": "Producto no encontrado"}), 404
            conn.commit()  # Confirmar la transacción
            
            print(f"DEBUG: Producto {pid} actualizado exitosamente")
            
            # Verificar si la columna porcentaje_descuento existe antes de hacer SELECT
            try:
                cursor_check = conn.cursor()
                cursor_check.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'productos' AND column_name = 'porcentaje_descuento'
                """)
                column_exists = cursor_check.fetchone() is not None
                
                if column_exists:
                    query = "SELECT id, name, brand, price, COALESCE(porcentaje_descuento, NULL) as porcentaje_descuento, category, sizes, stock, image, images, status, created_at, updated_at FROM productos WHERE id = %s"
                else:
                    print("WARNING: Usando query sin porcentaje_descuento")
                    query = "SELECT id, name, brand, price, NULL as porcentaje_descuento, category, sizes, stock, image, images, status, created_at, updated_at FROM productos WHERE id = %s"
                
                row = execute_query(conn, query, (pid,)).fetchone()
                print(f"DEBUG: Row obtenida: {row}")
                result = row_to_dict(row)
                print(f"DEBUG: Resultado final: {result}")
                return jsonify(result), 200
            except Exception as select_error:
                print(f"ERROR en SELECT: {select_error}")
                # Fallback: usar query básica
                row = execute_query(conn, "SELECT id, name, brand, price, category, sizes, stock, image, images, status, created_at, updated_at FROM productos WHERE id = %s", (pid,)).fetchone()
                if row:
                    # Agregar porcentaje_descuento como None
                    row_dict = row._asdict() if hasattr(row, '_asdict') else dict(zip(['id', 'name', 'brand', 'price', 'category', 'sizes', 'stock', 'image', 'images', 'status', 'created_at', 'updated_at'], row))
                    row_dict['porcentaje_descuento'] = None
                    result = row_to_dict(type('obj', (object,), row_dict)())
                    return jsonify(result), 200
                else:
                    return jsonify({"error": "Producto no encontrado después de actualizar"}), 404
        finally:
            conn.close()
    except Exception as e:
        print(f"ERROR en update_product: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500


@app.route("/api/products/<int:pid>", methods=["DELETE"])
def delete_product(pid: int):
    conn = get_conn()
    try:
        cur = execute_query(conn, "DELETE FROM productos WHERE id = %s", (pid,))
        if cur.rowcount == 0:
            return jsonify({"error": "Producto no encontrado"}), 404
        conn.commit()  # Confirmar la transacción
        return jsonify({"ok": True}), 200
    finally:
        conn.close()


@app.route("/api/products/<int:pid>/images", methods=["GET"])
def get_product_images(pid: int):
    """Obtener todas las imágenes de un producto"""
    conn = get_conn()
    try:
        row = execute_query(conn, "SELECT image, images FROM productos WHERE id = %s", (pid,)).fetchone()
        if not row:
            return jsonify({"error": "Producto no encontrado"}), 404
        
        product_dict = row_to_dict(row)
        all_images = [product_dict["image"]] + product_dict["images"]
        # Filtrar imágenes vacías
        all_images = [img for img in all_images if img and img.strip()]
        
        return jsonify({"images": all_images}), 200
    finally:
        conn.close()


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
        conn = get_conn()
        try:
            row = execute_query(conn, "SELECT images FROM productos WHERE id = %s", (pid,)).fetchone()
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
            execute_query(conn, "UPDATE productos SET images = %s WHERE id = %s", (images_json, pid))
            conn.commit()
            
            return jsonify({
                "success": True,
                "message": f"{len(uploaded_urls)} imágenes agregadas correctamente",
                "uploaded_urls": uploaded_urls,
                "total_images": len(all_images)
            }), 200
        finally:
            conn.close()
        
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
    conn = get_conn()
    try:
        for p in sample:
            execute_query(conn,
                """
                INSERT INTO productos (name, brand, price, category, sizes, stock, image, images, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    p["name"],
                    p["brand"],
                    float(p["price"]),
                    p["category"],
                    ",".join(p["sizes"]),
                    p["stock"],
                    p["image"],
                    "[]",  # images como JSON vacío
                    p["status"],
                ),
            )
        conn.commit()
        return jsonify({"ok": True, "inserted": len(sample)}), 201
    finally:
        conn.close()

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
        conn = get_conn()
        try:
            rows = execute_query(conn, "SELECT id, name, brand, price, COALESCE(porcentaje_descuento, NULL) as porcentaje_descuento, category, sizes, stock, image, images, status, created_at, updated_at FROM productos ORDER BY id DESC").fetchall()
            return jsonify([row_to_dict(r) for r in rows]), 200
        finally:
            conn.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------- RUTAS DE DEBUG ----------------------

@app.route("/api/debug/sessions", methods=["GET"])
def debug_sessions():
    """Debug: Ver todas las sesiones activas"""
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        # Obtener todas las sesiones
        cursor.execute("""
            SELECT s.token, s.expires_at, u.username, u.role
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            ORDER BY s.expires_at DESC
        """)
        sessions = cursor.fetchall()
        
        result = []
        for session in sessions:
            result.append({
                'token': session[0][:10] + '...',  # Solo mostrar los primeros 10 caracteres
                'expires_at': session[1].isoformat() if session[1] else None,
                'username': session[2],
                'role': session[3],
                'is_expired': session[1] < datetime.now() if session[1] else True
            })
        
        return jsonify({
            'total_sessions': len(result),
            'sessions': result
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route("/api/debug/validate-token", methods=["POST"])
def debug_validate_token():
    """Debug: Validar un token específico"""
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({"error": "Token requerido"}), 400
        
        # Validar el token usando el auth_manager
        user = auth_manager.validate_session(token)
        
        if user:
            return jsonify({
                "valid": True,
                "user": user
            }), 200
        else:
            return jsonify({
                "valid": False,
                "error": "Token inválido o expirado"
            }), 401
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/auth/refresh", methods=["POST"])
def refresh_token():
    """Renovar token de sesión"""
    try:
        data = request.get_json()
        old_token = data.get('token')
        
        if not old_token:
            return jsonify({"error": "Token requerido"}), 400
        
        # Validar el token actual
        user = auth_manager.validate_session(old_token)
        
        if user:
            # Crear nueva sesión
            new_token = auth_manager.create_session(user['user_id'])
            
            # Eliminar la sesión antigua
            auth_manager.logout_user(old_token)
            
            return jsonify({
                "success": True,
                "session_token": new_token,
                "user": user
            }), 200
        else:
            return jsonify({"error": "Token inválido o expirado"}), 401
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/debug/users", methods=["GET"])
def debug_users():
    """Debug: Ver todos los usuarios"""
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        # Obtener todos los usuarios
        cursor.execute("""
            SELECT id, username, role, nombre, apellido, email, created_at
            FROM users
            ORDER BY created_at DESC
        """)
        users = cursor.fetchall()
        
        result = []
        for user in users:
            result.append({
                'id': user[0],
                'username': user[1],
                'role': user[2],
                'nombre': user[3],
                'apellido': user[4],
                'email': user[5],
                'created_at': user[6].isoformat() if user[6] else None
            })
        
        return jsonify({
            'total_users': len(result),
            'users': result
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route("/api/debug/create-test-users", methods=["POST"])
def create_test_users():
    """Debug: Crear usuarios de prueba"""
    try:
        # Crear usuario admin
        admin_result = auth_manager.register_user(
            username="admin",
            password="admin123",
            email="admin@test.com",
            nombre="Admin",
            apellido="User",
            dni="12345678",
            telefono="1234567890",
            direccion="Calle Admin 123",
            codigo_postal="1234"
        )
        
        # Crear usuario normal
        user_result = auth_manager.register_user(
            username="usuario",
            password="user123",
            email="usuario@test.com",
            nombre="Usuario",
            apellido="Test",
            dni="87654321",
            telefono="0987654321",
            direccion="Calle Usuario 456",
            codigo_postal="5678"
        )
        
        # Actualizar rol del admin
        if admin_result.get("success"):
            conn = get_conn()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET role = 'admin' WHERE username = 'admin'")
            conn.commit()
            conn.close()
        
        return jsonify({
            "admin_created": admin_result.get("success", False),
            "user_created": user_result.get("success", False),
            "admin_message": admin_result.get("message", admin_result.get("error", "")),
            "user_message": user_result.get("message", user_result.get("error", ""))
        }), 200
        
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