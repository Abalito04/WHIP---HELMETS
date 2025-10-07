from flask import Flask, request, jsonify, send_from_directory, g, session, make_response
from flask_cors import CORS
from functools import wraps
import os
import re
from database import get_conn, init_postgresql
from datetime import datetime, timedelta
import hashlib
import secrets

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

# Importar el servicio de email (Resend)
try:
    from resend_service import resend_email_service as email_service
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False
    print("⚠️  Módulo de email no disponible")

# Importar utilidades SEO
try:
    from seo_utils import SEOUtils
    seo_utils = SEOUtils()
    SEO_AVAILABLE = True
except ImportError:
    SEO_AVAILABLE = False
    print("⚠️  Módulo SEO no disponible")

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
    """Verifica rate limiting mejorado"""
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

def get_rate_limits():
    """Obtener límites de rate limiting según configuración"""
    return {
        'login': int(os.environ.get('RATE_LIMIT_LOGIN', 3)),  # 3 intentos por defecto
        'register': int(os.environ.get('RATE_LIMIT_REGISTER', 2)),  # 2 intentos por defecto
        'payment': int(os.environ.get('RATE_LIMIT_PAYMENT', 5)),  # 5 intentos por defecto
        'api': int(os.environ.get('RATE_LIMIT_API', 60)),  # 60 requests por defecto
    }

def debug_only(f):
    """Decorador para endpoints que solo funcionan en modo debug/desarrollo"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificar si estamos en modo debug o desarrollo
        is_debug = app.config.get('DEBUG', False)
        is_dev = os.environ.get('ENABLE_DEBUG_ENDPOINTS', 'False').lower() == 'true'
        
        if not is_debug and not is_dev:
            return jsonify({
                "error": "Endpoint no disponible en producción",
                "message": "Los endpoints de debug están deshabilitados por seguridad"
            }), 403
        
        return f(*args, **kwargs)
    return decorated_function

# ---------------------- Protección CSRF ----------------------

def generate_csrf_token():
    """Generar token CSRF único"""
    return secrets.token_urlsafe(32)

def validate_csrf_token(token):
    """Validar token CSRF"""
    if not token:
        return False
    
    # En una implementación más robusta, podrías almacenar tokens en la base de datos
    # Para esta implementación básica, validamos que el token tenga el formato correcto
    return len(token) >= 32 and token.replace('-', '').replace('_', '').isalnum()

def require_csrf(f):
    """Decorador para requerir token CSRF en endpoints POST"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Solo aplicar CSRF a métodos POST, PUT, DELETE
        if request.method in ['POST', 'PUT', 'DELETE']:
            # Obtener token del header o del JSON
            csrf_token = request.headers.get('X-CSRF-Token') or request.get_json().get('csrf_token') if request.get_json() else None

            if not validate_csrf_token(csrf_token):
                return jsonify({
                    "error": "Token CSRF inválido o faltante",
                    "message": "Se requiere un token CSRF válido para esta operación"
                }), 403

        return f(*args, **kwargs)
    return decorated_function

def require_csrf_file_upload(f):
    """Decorador para requerir token CSRF en endpoints de subida de archivos"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Solo aplicar CSRF a métodos POST, PUT, DELETE
        if request.method in ['POST', 'PUT', 'DELETE']:
            # Para archivos, obtener token del header o del form data
            csrf_token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')

            if not validate_csrf_token(csrf_token):
                return jsonify({
                    "error": "Token CSRF inválido o faltante",
                    "message": "Se requiere un token CSRF válido para esta operación"
                }), 403

        return f(*args, **kwargs)
    return decorated_function

app = Flask(__name__)
app.config['DEBUG'] = os.environ.get('DEBUG', 'False').lower() == 'true'

# Configurar SECRET_KEY para sesiones y CSRF
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
# Configurar CORS de forma más segura
def configure_cors():
    """Configurar CORS según el entorno"""
    # Detectar si estamos en Railway (producción)
    is_production = not app.config['DEBUG'] or os.environ.get('IS_PRODUCTION', 'False').lower() == 'true'
    
    if is_production:
        # En producción, usar orígenes específicos
        railway_url = os.environ.get('RAILWAY_STATIC_URL', '')
        public_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', '')
        custom_origins = os.environ.get('CORS_ORIGINS', '').split(',')
        
        # Construir lista de orígenes permitidos
        allowed_origins = []
        
        if railway_url:
            allowed_origins.append(railway_url)
        if public_domain:
            allowed_origins.append(f"https://{public_domain}")
        if custom_origins and custom_origins != ['']:
            allowed_origins.extend(custom_origins)
        
        # Si no hay orígenes específicos, usar el dominio de Railway detectado
        if not allowed_origins:
            # Detectar automáticamente desde el host
            allowed_origins = ['https://whip-helmets.up.railway.app']
        
        print(f"🔒 CORS configurado para producción: {allowed_origins}")
        CORS(app, origins=allowed_origins, supports_credentials=True)
    else:
        # En desarrollo, permitir cualquier origen
        print("🔓 CORS configurado para desarrollo: permitir todos los orígenes")
        CORS(app, supports_credentials=True)

configure_cors()

# ---------------------- Headers de Seguridad ----------------------
@app.after_request
def add_security_headers(response):
    """Agregar headers de seguridad básicos"""
    # Prevenir MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # Protección básica contra clickjacking (permisivo para MercadoPago)
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    
    # Protección XSS básica
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Política de referrer (privacidad)
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Content Security Policy básico
    csp_policy = generate_csp_policy()
    response.headers['Content-Security-Policy'] = csp_policy
    
    # Solo en producción: HTTPS obligatorio
    if not app.config['DEBUG']:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    return response

def generate_csp_policy():
    """Generar Content Security Policy según el entorno"""
    is_production = not app.config['DEBUG'] or os.environ.get('IS_PRODUCTION', 'False').lower() == 'true'
    
    if is_production:
        # CSP estricto para producción
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' https://sdk.mercadopago.com https://www.mercadopago.com",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com",
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com",
            "img-src 'self' data: blob: https: http:",
            "connect-src 'self' https://api.mercadopago.com https://whip-helmets.up.railway.app",
            "frame-src 'self' https://www.mercadopago.com",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ]
    else:
        # CSP permisivo para desarrollo
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
            "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com",
            "font-src 'self' https://cdnjs.cloudflare.com",
            "img-src 'self' data: blob: https: http:",
            "connect-src 'self' http://localhost:* https://localhost:*",
            "frame-src 'self'",
            "object-src 'none'"
        ]
    
    return "; ".join(csp_directives)

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
        
        # Ejecutar migración completa de base de datos
        try:
            print("🔄 Ejecutando migración de base de datos...")
            from migrate_database import create_orders_table, create_order_items_table, add_verification_code_column
            
            create_orders_table()
            create_order_items_table()
            add_verification_code_column()
            
            print("✅ Migración de base de datos completada")
                    
        except Exception as e:
            print(f"⚠️  Error en migración de base de datos: {e}")
            # Intentar migración individual de verification_code como respaldo
            try:
                print("🔄 Intentando migración individual de verification_code...")
                from database import get_conn
                with get_conn() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_name = 'orders' AND column_name = 'verification_code'
                    """)
                    if not cursor.fetchone():
                        cursor.execute("ALTER TABLE orders ADD COLUMN verification_code VARCHAR(20)")
                        cursor.execute("""
                            UPDATE orders 
                            SET verification_code = UPPER(SUBSTRING(MD5(order_number || EXTRACT(EPOCH FROM created_at)::text), 1, 8))
                            WHERE verification_code IS NULL
                        """)
                        conn.commit()
                        print("✅ Columna verification_code agregada como respaldo")
            except Exception as backup_error:
                print(f"⚠️  Error en migración de respaldo: {backup_error}")
            # No fallar el inicio del servidor por esto
            
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
        columns = ['id', 'name', 'brand', 'price', 'porcentaje_descuento', 'category', 'condition', 'sizes', 'stock', 'image', 'images', 'status']
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
    
    # Si no existe precio_efectivo en la base de datos, calcularlo
    if "precio_efectivo" not in d:
        if d.get("porcentaje_descuento") and d["porcentaje_descuento"] > 0:
            descuento = d["price"] * (d["porcentaje_descuento"] / 100)
            d["precio_efectivo"] = round(d["price"] - descuento, 2)
        else:
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

@app.route("/api/csrf-token", methods=["GET"])
def get_csrf_token():
    """Obtener token CSRF para formularios"""
    token = generate_csrf_token()
    return jsonify({
        "csrf_token": token,
        "message": "Token CSRF generado correctamente"
    }), 200

@app.route("/api/email/status", methods=["GET"])
def get_email_status():
    """Verificar estado del sistema de email"""
    if not EMAIL_AVAILABLE:
        return jsonify({
            "available": False,
            "message": "Módulo de email no disponible"
        }), 503
    
    # Información detallada del estado
    status_info = {
        "available": EMAIL_AVAILABLE,
        "configured": email_service.is_configured,
        "service": "Resend",
        "from_email": email_service.from_email,
        "from_name": email_service.from_name,
        "api_key_set": bool(email_service.api_key),
        "api_key_length": len(email_service.api_key) if email_service.api_key else 0
    }
    
    if email_service.is_configured:
        status_info["message"] = "Sistema de email configurado correctamente"
    else:
        status_info["message"] = "Sistema de email no configurado - configurar RESEND_API_KEY"
    
    return jsonify(status_info), 200

@app.route("/api/email/test-welcome", methods=["POST"])
def test_welcome_email():
    """Endpoint de prueba para enviar email de bienvenida"""
    if not EMAIL_AVAILABLE:
        return jsonify({
            "success": False,
            "message": "Módulo de email no disponible"
        }), 503
    
    if not email_service.is_configured:
        return jsonify({
            "success": False,
            "message": "Sistema de email no configurado - configurar RESEND_API_KEY"
        }), 503
    
    try:
        data = request.get_json()
        test_email = data.get('email', 'test@example.com')
        test_name = data.get('name', 'Usuario de Prueba')
        
        success, message = email_service.send_welcome_email(test_email, test_name)
        
        return jsonify({
            "success": success,
            "message": message,
            "test_email": test_email,
            "test_name": test_name
        }), 200 if success else 500
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error en prueba de email: {str(e)}"
        }), 500

@app.route("/api/seo/meta", methods=["GET"])
def get_seo_meta():
    """Obtener meta tags SEO para una página"""
    if not SEO_AVAILABLE:
        return jsonify({
            "available": False,
            "message": "Módulo SEO no disponible"
        }), 503
    
    try:
        page_type = request.args.get('type', 'homepage')
        product_id = request.args.get('product_id')
        category = request.args.get('category')
        
        if page_type == 'product' and product_id:
            # Obtener datos del producto
            conn = get_conn()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, description, price, stock, image
                    FROM productos 
                    WHERE id = %s
                """, (product_id,))
                product = cursor.fetchone()
                
                if product:
                    product_data = {
                        'id': product[0],
                        'name': product[1],
                        'description': product[2],
                        'price': float(product[3]),
                        'stock': product[4],
                        'image': product[5]
                    }
                    meta_data = seo_utils.get_product_meta(product_data)
                    structured_data = seo_utils.generate_structured_data('product', product_data)
                else:
                    meta_data = seo_utils.get_homepage_meta()
                    structured_data = seo_utils.generate_structured_data()
            finally:
                conn.close()
                
        elif page_type == 'category' and category:
            meta_data = seo_utils.get_category_meta(category)
            structured_data = seo_utils.generate_structured_data()
            
        elif page_type == 'contact':
            meta_data = seo_utils.get_contact_meta()
            structured_data = seo_utils.generate_structured_data()
            
        else:  # homepage
            meta_data = seo_utils.get_homepage_meta()
            structured_data = seo_utils.generate_structured_data()
        
        return jsonify({
            "available": True,
            "meta": meta_data,
            "structured_data": structured_data,
            "message": "Meta tags generados correctamente"
        }), 200
        
    except Exception as e:
        return jsonify({
            "available": False,
            "message": f"Error generando meta tags: {str(e)}"
        }), 500

@app.route("/sitemap.xml", methods=["GET"])
def sitemap():
    """Generar sitemap.xml automático"""
    if not SEO_AVAILABLE:
        return "Sitemap no disponible", 503
    
    try:
        base_url = seo_utils.base_url
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        # Páginas estáticas
        static_pages = [
            {'url': '', 'priority': '1.0', 'changefreq': 'daily'},
            {'url': '/checkout', 'priority': '0.8', 'changefreq': 'monthly'},
            {'url': '/orders', 'priority': '0.7', 'changefreq': 'monthly'},
            {'url': '/profile', 'priority': '0.6', 'changefreq': 'monthly'},
            {'url': '/register', 'priority': '0.5', 'changefreq': 'yearly'},
            {'url': '/forgot-password', 'priority': '0.3', 'changefreq': 'yearly'},
            {'url': '/reset-password', 'priority': '0.3', 'changefreq': 'yearly'},
            {'url': '/pages/politica-de-privacidad', 'priority': '0.4', 'changefreq': 'yearly'},
            {'url': '/pages/terminos-y-condiciones', 'priority': '0.4', 'changefreq': 'yearly'}
        ]
        
        # Obtener productos
        conn = get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, updated_at
                FROM productos 
                ORDER BY id DESC
            """)
            products = cursor.fetchall()
        finally:
            conn.close()
        
        # Generar XML
        xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        
        # Agregar páginas estáticas
        for page in static_pages:
            xml_content += f'  <url>\n'
            xml_content += f'    <loc>{base_url}{page["url"]}</loc>\n'
            xml_content += f'    <lastmod>{current_date}</lastmod>\n'
            xml_content += f'    <changefreq>{page["changefreq"]}</changefreq>\n'
            xml_content += f'    <priority>{page["priority"]}</priority>\n'
            xml_content += f'  </url>\n'
        
        # Agregar productos
        for product in products:
            product_id, product_name, updated_at = product
            lastmod = updated_at.strftime('%Y-%m-%d') if updated_at else current_date
            xml_content += f'  <url>\n'
            xml_content += f'    <loc>{base_url}/producto/{product_id}</loc>\n'
            xml_content += f'    <lastmod>{lastmod}</lastmod>\n'
            xml_content += f'    <changefreq>weekly</changefreq>\n'
            xml_content += f'    <priority>0.8</priority>\n'
            xml_content += f'  </url>\n'
        
        xml_content += '</urlset>'
        
        response = make_response(xml_content)
        response.headers['Content-Type'] = 'application/xml'
        return response
        
    except Exception as e:
        return f"Error generando sitemap: {str(e)}", 500

@app.route("/robots.txt", methods=["GET"])
def robots():
    """Generar robots.txt"""
    if not SEO_AVAILABLE:
        return "Robots.txt no disponible", 503
    
    try:
        base_url = seo_utils.base_url
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        robots_content = f"""User-agent: *
Allow: /
Disallow: /admin/
Disallow: /api/
Disallow: /backend/
Disallow: /payment/
Disallow: /test-chatbot.html

Sitemap: {base_url}/sitemap.xml

# WHIP HELMETS - Cascos y Accesorios de Motociclismo
# Generado automáticamente el {current_date}
"""
        
        response = make_response(robots_content)
        response.headers['Content-Type'] = 'text/plain'
        return response
        
    except Exception as e:
        return f"Error generando robots.txt: {str(e)}", 500

@app.route("/api/migrate/password-reset", methods=["POST"])
@debug_only
def migrate_password_reset():
    """Ejecutar migración de password_reset_tokens"""
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        # Leer el archivo SQL
        with open('backend/migrate_password_reset.sql', 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Ejecutar la migración
        cursor.execute(sql_content)
        conn.commit()
        
        # Verificar que la tabla se creó
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'password_reset_tokens'
        """)
        
        if cursor.fetchone():
            return jsonify({
                "success": True,
                "message": "Tabla 'password_reset_tokens' creada exitosamente"
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "Error: Tabla no se creó"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error ejecutando migración: {str(e)}"
        }), 500
    finally:
        conn.close()


@app.route("/api/auth/forgot-password", methods=["POST"])
@require_csrf
def forgot_password():
    """Solicitar recuperación de contraseña"""
    if not AUTH_AVAILABLE:
        return jsonify({"error": "Sistema de autenticación no disponible"}), 503
    
    try:
        # Rate limiting para recuperación de contraseña
        client_ip = request.remote_addr
        rate_limits = get_rate_limits()
        
        if not check_rate_limit(client_ip, 'forgot_password', limit=3, window=3600):  # 3 intentos por hora
            return jsonify({"error": "Demasiados intentos. Intenta en 1 hora."}), 429
        
        data = request.get_json()
        email = sanitize_input(data.get('email', ''))
        
        if not email:
            return jsonify({"error": "Email requerido"}), 400
        
        # Validar formato de email
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return jsonify({"error": "Formato de email inválido"}), 400
        
        # Buscar usuario por email
        conn = get_conn()
        try:
            cursor = conn.cursor()
            
            # Crear tabla si no existe
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS password_reset_tokens (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    token VARCHAR(255) NOT NULL UNIQUE,
                    email VARCHAR(255) NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    used BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Crear índices si no existen
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_token 
                ON password_reset_tokens(token)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_user_id 
                ON password_reset_tokens(user_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_expires_at 
                ON password_reset_tokens(expires_at)
            """)
            
            cursor.execute("""
                SELECT id, username, email, nombre, apellido 
                FROM users 
                WHERE email = %s
            """, (email,))
            user = cursor.fetchone()
            
            if not user:
                # Por seguridad, no revelar si el email existe o no
                return jsonify({
                    "success": True,
                    "message": "Si el email existe, recibirás un enlace de recuperación"
                }), 200
            
            # Generar token de recuperación
            import secrets
            import hashlib
            from datetime import datetime, timedelta
            
            # Crear token único
            token = secrets.token_urlsafe(32)
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            
            # Expira en 1 hora
            expires_at = datetime.now() + timedelta(hours=1)
            
            # Limpiar tokens anteriores del usuario
            cursor.execute("""
                DELETE FROM password_reset_tokens 
                WHERE user_id = %s OR email = %s
            """, (user[0], email))  # user[0] es el id
            
            # Insertar nuevo token
            cursor.execute("""
                INSERT INTO password_reset_tokens (user_id, token, email, expires_at)
                VALUES (%s, %s, %s, %s)
            """, (user[0], token_hash, email, expires_at))  # user[0] es el id
            
            conn.commit()
            
            # Enviar email de recuperación
            if EMAIL_AVAILABLE:
                try:
                    customer_name = f"{user[3] or ''} {user[4] or ''}".strip()  # user[3] es nombre, user[4] es apellido
                    if not customer_name:
                        customer_name = user[1] or 'Usuario'  # user[1] es username
                    
                    success, message = email_service.send_password_reset(
                        email,
                        customer_name,
                        token  # Enviar token sin hashear
                    )
                    
                    if success:
                        print(f"✅ Email de recuperación enviado a {email}")
                    else:
                        print(f"⚠️  Error enviando email de recuperación: {message}")
                        
                except Exception as e:
                    print(f"⚠️  Error en envío de email de recuperación: {e}")
                    # No fallar el proceso por error de email
            
            return jsonify({
                "success": True,
                "message": "Si el email existe, recibirás un enlace de recuperación"
            }), 200
            
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/auth/reset-password", methods=["POST"])
@require_csrf
def reset_password():
    """Restablecer contraseña con token"""
    if not AUTH_AVAILABLE:
        return jsonify({"error": "Sistema de autenticación no disponible"}), 503
    
    try:
        data = request.get_json()
        token = data.get('token', '')
        new_password = data.get('new_password', '')
        
        if not token or not new_password:
            return jsonify({"error": "Token y nueva contraseña requeridos"}), 400
        
        # Validar longitud de contraseña
        if len(new_password) < 8:
            return jsonify({"error": "La contraseña debe tener al menos 8 caracteres"}), 400
        
        # Validar que la contraseña contenga letras y números
        has_letter = any(c.isalpha() for c in new_password)
        has_number = any(c.isdigit() for c in new_password)
        if not (has_letter and has_number):
            return jsonify({"error": "La contraseña debe contener al menos una letra y un número"}), 400
        
        # Buscar token válido
        import hashlib
        from datetime import datetime
        
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        conn = get_conn()
        try:
            cursor = conn.cursor()
            
            # Crear tabla si no existe
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS password_reset_tokens (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    token VARCHAR(255) NOT NULL UNIQUE,
                    email VARCHAR(255) NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    used BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            cursor.execute("""
                SELECT prt.id, prt.user_id, prt.email, prt.expires_at, prt.used,
                       u.username, u.nombre, u.apellido
                FROM password_reset_tokens prt
                JOIN users u ON prt.user_id = u.id
                WHERE prt.token = %s
            """, (token_hash,))
            
            reset_token = cursor.fetchone()
            
            if not reset_token:
                return jsonify({"error": "Token inválido"}), 400
            
            if reset_token[4]:  # reset_token[4] es used
                return jsonify({"error": "Token ya utilizado"}), 400
            
            if datetime.now() > reset_token[3]:  # reset_token[3] es expires_at
                return jsonify({"error": "Token expirado"}), 400
            
            # Actualizar contraseña del usuario
            import hashlib
            password_hash = hashlib.sha256(new_password.encode()).hexdigest()
            
            cursor.execute("""
                UPDATE users 
                SET password_hash = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (password_hash, reset_token[1]))  # reset_token[1] es user_id
            
            # Marcar token como usado
            cursor.execute("""
                UPDATE password_reset_tokens 
                SET used = TRUE 
                WHERE id = %s
            """, (reset_token[0],))  # reset_token[0] es id
            
            conn.commit()
            
            print(f"✅ Contraseña restablecida para usuario {reset_token[5]}")  # reset_token[5] es username
            
            return jsonify({
                "success": True,
                "message": "Contraseña restablecida exitosamente"
            }), 200
            
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/auth/status", methods=["GET"])
def auth_status():
    """Verificar estado de autenticación del usuario"""
    try:
        user_id = session.get('user_id')
        username = session.get('username')
        
        if user_id and username:
            return jsonify({
                "authenticated": True,
                "user_id": user_id,
                "username": username
            }), 200
        else:
            return jsonify({
                "authenticated": False,
                "message": "Usuario no autenticado"
            }), 401
            
    except Exception as e:
        return jsonify({
            "authenticated": False,
            "error": str(e)
        }), 500

@app.route("/api/auth/validate-reset-token", methods=["POST"])
def validate_reset_token():
    """Validar si un token de recuperación es válido"""
    try:
        data = request.get_json()
        token = data.get('token', '')
        
        if not token:
            return jsonify({"error": "Token requerido"}), 400
        
        import hashlib
        from datetime import datetime
        
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        conn = get_conn()
        try:
            cursor = conn.cursor()
            
            # Crear tabla si no existe
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS password_reset_tokens (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    token VARCHAR(255) NOT NULL UNIQUE,
                    email VARCHAR(255) NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    used BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            cursor.execute("""
                SELECT prt.expires_at, prt.used, u.username
                FROM password_reset_tokens prt
                JOIN users u ON prt.user_id = u.id
                WHERE prt.token = %s
            """, (token_hash,))
            
            reset_token = cursor.fetchone()
            
            if not reset_token:
                return jsonify({
                    "valid": False,
                    "message": "Token inválido"
                }), 400
            
            if reset_token[1]:  # reset_token[1] es used
                return jsonify({
                    "valid": False,
                    "message": "Token ya utilizado"
                }), 400
            
            if datetime.now() > reset_token[0]:  # reset_token[0] es expires_at
                return jsonify({
                    "valid": False,
                    "message": "Token expirado"
                }), 400
            
            return jsonify({
                "valid": True,
                "message": "Token válido",
                "username": reset_token[2]  # reset_token[2] es username
            }), 200
            
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500



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

        query = "SELECT id, name, brand, price, COALESCE(porcentaje_descuento, NULL) as porcentaje_descuento, category, condition, sizes, stock, image, images, status, created_at, updated_at FROM productos WHERE 1=1"
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
        row = execute_query(conn, "SELECT id, name, brand, price, COALESCE(porcentaje_descuento, NULL) as porcentaje_descuento, category, condition, sizes, stock, image, images, status, created_at, updated_at FROM productos WHERE id = %s", (pid,)).fetchone()
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
    precio_efectivo = data.get("precio_efectivo")
    porcentaje_descuento = data.get("porcentaje_descuento")
    if not name:
        return jsonify({"error": "El campo 'name' es obligatorio"}), 400
    try:
        price = float(price)
    except Exception:
        return jsonify({"error": "El campo 'price' debe ser numérico"}), 400
    
    # Validar precio_efectivo si se proporciona
    if precio_efectivo is not None:
        try:
            precio_efectivo = float(precio_efectivo)
            if precio_efectivo < 0:
                return jsonify({"error": "El precio efectivo debe ser mayor o igual a 0"}), 400
        except Exception:
            return jsonify({"error": "El campo 'precio_efectivo' debe ser numérico"}), 400
    
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
    condition = (data.get("condition") or "Nuevo").strip()
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
        # Verificar si la columna precio_efectivo existe
        try:
            cursor_check = conn.cursor()
            cursor_check.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'productos' AND column_name = 'precio_efectivo'
            """)
            precio_efectivo_exists = cursor_check.fetchone() is not None
        except Exception:
            precio_efectivo_exists = False
        
        cursor = conn.cursor()
        
        if precio_efectivo_exists:
            cursor.execute(
                """
                INSERT INTO productos (name, brand, price, precio_efectivo, porcentaje_descuento, category, condition, sizes, stock, image, images, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (name, brand, price, precio_efectivo, porcentaje_descuento, category, condition, sizes_csv, stock, image, images_json, status),
            )
        else:
            cursor.execute(
                """
                INSERT INTO productos (name, brand, price, porcentaje_descuento, category, condition, sizes, stock, image, images, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (name, brand, price, porcentaje_descuento, category, condition, sizes_csv, stock, image, images_json, status),
            )
        
        # PostgreSQL: obtener el ID del último insert
        result = cursor.fetchone()
        new_id = result[0]  # Acceder por índice en lugar de por clave
        conn.commit()  # Confirmar la transacción

        cursor.execute("SELECT id, name, brand, price, COALESCE(porcentaje_descuento, NULL) as porcentaje_descuento, category, condition, sizes, stock, image, images, status, created_at, updated_at FROM productos WHERE id = %s", (new_id,))
        row = cursor.fetchone()
        
        # Convertir a diccionario manualmente
        columns = ['id', 'name', 'brand', 'price', 'porcentaje_descuento', 'category', 'condition', 'sizes', 'stock', 'image', 'images', 'status', 'created_at', 'updated_at']
        row_dict = {}
        for i, col in enumerate(columns):
            if i < len(row):
                row_dict[col] = row[i]
        
        return jsonify(row_dict), 201
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

        if "precio_efectivo" in data:
            precio_efectivo = data.get("precio_efectivo")
            if precio_efectivo is not None and precio_efectivo != "":
                try:
                    precio_efectivo = float(precio_efectivo)
                    if precio_efectivo < 0:
                        return jsonify({"error": "El precio efectivo debe ser mayor o igual a 0"}), 400
                except Exception:
                    return jsonify({"error": "El campo 'precio_efectivo' debe ser numérico"}), 400
            # Verificar si la columna existe antes de intentar actualizarla
            try:
                cursor_check = conn.cursor()
                cursor_check.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'productos' AND column_name = 'precio_efectivo'
                """)
                column_exists = cursor_check.fetchone() is not None
                if column_exists:
                    set_field("precio_efectivo", precio_efectivo)
                else:
                    print(f"WARNING: Columna precio_efectivo no existe, saltando actualización")
            except Exception as e:
                print(f"WARNING: Error verificando columna precio_efectivo: {e}")
                # Si no podemos verificar, no intentar actualizar
                print(f"WARNING: No se puede verificar la columna precio_efectivo, saltando actualización")

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

        if "condition" in data:
            set_field("condition", (data.get("condition") or "").strip())

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
                    query = "SELECT id, name, brand, price, COALESCE(porcentaje_descuento, NULL) as porcentaje_descuento, category, condition, sizes, stock, image, images, status, created_at, updated_at FROM productos WHERE id = %s"
                else:
                    print("WARNING: Usando query sin porcentaje_descuento")
                    query = "SELECT id, name, brand, price, NULL as porcentaje_descuento, category, condition, sizes, stock, image, images, status, created_at, updated_at FROM productos WHERE id = %s"
                
                row = execute_query(conn, query, (pid,)).fetchone()
                print(f"DEBUG: Row obtenida: {row}")
                result = row_to_dict(row)
                print(f"DEBUG: Resultado final: {result}")
                return jsonify(result), 200
            except Exception as select_error:
                print(f"ERROR en SELECT: {select_error}")
                # Fallback: usar query básica
                row = execute_query(conn, "SELECT id, name, brand, price, category, condition, sizes, stock, image, images, status, created_at, updated_at FROM productos WHERE id = %s", (pid,)).fetchone()
                if row:
                    # Agregar campos faltantes como None
                    row_dict = row._asdict() if hasattr(row, '_asdict') else dict(zip(['id', 'name', 'brand', 'price', 'category', 'sizes', 'stock', 'image', 'images', 'status', 'created_at', 'updated_at'], row))
                    row_dict['precio_efectivo'] = row_dict.get('price', 0)
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
@require_csrf_file_upload
def add_product_images(pid: int):
    """Agregar nuevas imágenes a un producto con validación de seguridad"""
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
            
            # Validación de seguridad mejorada
            is_valid, message = validate_file_security(file)
            if not is_valid:
                print(f"Archivo rechazado: {file.filename} - {message}")
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

# ---------------------- VALIDACIÓN DE ARCHIVOS MEJORADA ----------------------

def validate_file_security(file):
    """Validación de seguridad mejorada para archivos"""
    import imghdr
    
    # Intentar importar magic, si no está disponible usar validación básica
    try:
        import magic
        MAGIC_AVAILABLE = True
    except ImportError:
        MAGIC_AVAILABLE = False
        print("⚠️  python-magic no disponible, usando validación básica")
    
    # 1. Validar que el archivo existe
    if not file or file.filename == '':
        return False, "No se seleccionó archivo"
    
    # 2. Validar extensión del archivo
    allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.tiff'}
    file_extension = os.path.splitext(file.filename.lower())[1]
    if file_extension not in allowed_extensions:
        return False, f"Extensión de archivo no permitida: {file_extension}"
    
    # 3. Validar tamaño del archivo (máximo 10MB)
    file.seek(0, 2)  # Ir al final del archivo
    file_size = file.tell()
    file.seek(0)  # Volver al inicio
    
    max_size = 10 * 1024 * 1024  # 10MB
    if file_size > max_size:
        return False, f"Archivo demasiado grande. Máximo permitido: 10MB, recibido: {file_size / (1024*1024):.1f}MB"
    
    # 4. Validar que el archivo no esté vacío
    if file_size == 0:
        return False, "El archivo está vacío"
    
    # 5. Validar MIME type real del archivo
    try:
        # Leer los primeros bytes para detectar el tipo real
        file.seek(0)
        file_header = file.read(1024)
        file.seek(0)
        
        # Detectar tipo MIME real
        if MAGIC_AVAILABLE:
            mime_type = magic.from_buffer(file_header, mime=True)
            allowed_mime_types = {
                'image/png', 'image/jpeg', 'image/gif', 'image/webp', 
                'image/bmp', 'image/tiff', 'image/x-icon'
            }
            
            if mime_type not in allowed_mime_types:
                return False, f"Tipo de archivo no permitido: {mime_type}"
        else:
            # Validación básica sin magic
            print("⚠️  Validación MIME básica (python-magic no disponible)")
        
        # 6. Validación adicional con imghdr
        file.seek(0)
        detected_format = imghdr.what(file)
        file.seek(0)
        
        if not detected_format:
            return False, "El archivo no es una imagen válida"
        
        # 7. Verificar que la extensión coincida con el contenido real
        extension_to_format = {
            '.png': 'png', '.jpg': 'jpeg', '.jpeg': 'jpeg', 
            '.gif': 'gif', '.webp': 'webp', '.bmp': 'bmp', '.tiff': 'tiff'
        }
        
        expected_format = extension_to_format.get(file_extension)
        if expected_format and detected_format != expected_format:
            return False, f"La extensión del archivo no coincide con su contenido real"
        
        return True, "Archivo válido"
        
    except Exception as e:
        return False, f"Error al validar el archivo: {str(e)}"

def sanitize_filename(filename):
    """Sanitizar nombre de archivo para evitar path traversal"""
    import re
    
    # Remover caracteres peligrosos
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    
    # Remover puntos al inicio (path traversal)
    filename = filename.lstrip('.')
    
    # Limitar longitud
    if len(filename) > 100:
        name, ext = os.path.splitext(filename)
        filename = name[:95] + ext
    
    return filename

# ---------------------- SUBIDA DE IMÁGENES ----------------------

@app.route("/api/upload", methods=["POST"])
@require_csrf_file_upload
def upload_image():
    """Endpoint para subir imágenes con validación de seguridad mejorada"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No se encontró archivo"}), 400
        
        file = request.files['file']
        
        # Validación de seguridad mejorada
        is_valid, message = validate_file_security(file)
        if not is_valid:
            return jsonify({"error": message}), 400
        
        # Sanitizar nombre de archivo
        sanitized_filename = sanitize_filename(file.filename)
        
        # Verificar configuración de Cloudinary
        if not CLOUDINARY_CLOUD_NAME or not CLOUDINARY_API_KEY or not CLOUDINARY_API_SECRET:
            # Modo temporal: guardar en local y devolver URL relativa
            import uuid
            
            # Crear directorio si no existe
            upload_dir = "../assets/images/products/uploaded"
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generar nombre único con extensión segura
            file_extension = os.path.splitext(sanitized_filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(upload_dir, unique_filename)
            
            # Guardar archivo
            file.save(file_path)
            
            # Devolver URL relativa
            relative_path = f"assets/images/products/uploaded/{unique_filename}"
            
            return jsonify({
                "success": True,
                "message": "Imagen subida correctamente (modo temporal)",
                "file_path": relative_path,
                "filename": sanitized_filename,
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
            "filename": sanitized_filename
        }), 200
        
    except Exception as e:
        print(f"Error al subir imagen a Cloudinary: {e}")
        return jsonify({"error": f"Error al subir imagen: {str(e)}"}), 500


# ---------------------- RUTAS DE AUTENTICACIÓN ----------------------

@app.route("/api/auth/register", methods=["POST"])
@require_csrf
def auth_register():
    """Endpoint para registro de nuevos usuarios con rate limiting"""
    if not AUTH_AVAILABLE:
        return jsonify({"error": "Sistema de autenticación no disponible"}), 503
    
    try:
        # Rate limiting para registro
        client_ip = request.remote_addr
        rate_limits = get_rate_limits()
        
        if not check_rate_limit(client_ip, 'register', limit=rate_limits['register'], window=600):
            return jsonify({"error": "Demasiados intentos de registro. Intenta en 10 minutos."}), 429
        
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        profile_data = data.get('profile', {})
        
        # Validar campos requeridos
        if not username or not password:
            return jsonify({"error": "Usuario y contraseña son requeridos"}), 400
        
        # Validar longitud de contraseña (mínimo 8 caracteres)
        if len(password) < 8:
            return jsonify({"error": "La contraseña debe tener al menos 8 caracteres"}), 400
        
        # Validar que la contraseña contenga letras y números
        has_letter = any(c.isalpha() for c in password)
        has_number = any(c.isdigit() for c in password)
        if not (has_letter and has_number):
            return jsonify({"error": "La contraseña debe contener al menos una letra y un número"}), 400
        
        # Validar campos del perfil si se proporcionan
        required_fields = ['nombre', 'apellido', 'dni', 'telefono', 'email']
        for field in required_fields:
            if not profile_data.get(field):
                return jsonify({"error": f"Campo {field} es requerido"}), 400
        
        # Validar formato de email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, profile_data['email']):
            return jsonify({"error": "Formato de email inválido"}), 400
        
        # Validar DNI (exactamente 8 dígitos)
        if not profile_data['dni'].isdigit() or len(profile_data['dni']) != 8:
            return jsonify({"error": "DNI debe contener exactamente 8 números"}), 400
        
        # Validar teléfono (solo números)
        if not profile_data['telefono'].isdigit():
            return jsonify({"error": "Teléfono debe contener solo números"}), 400
        
        # Validar código postal (4 o 5 dígitos)
        if profile_data.get('codigo_postal'):
            if not profile_data['codigo_postal'].isdigit() or len(profile_data['codigo_postal']) < 4 or len(profile_data['codigo_postal']) > 5:
                return jsonify({"error": "Código postal debe contener entre 4 y 5 números"}), 400
        
        result = auth_manager.register_user(username, password, **profile_data)
        
        if result['success']:
            # Enviar email de bienvenida si está disponible
            if EMAIL_AVAILABLE and profile_data.get('email'):
                try:
                    customer_name = f"{profile_data.get('nombre', '')} {profile_data.get('apellido', '')}".strip()
                    if not customer_name:
                        customer_name = username
                    
                    print(f"🔄 Intentando enviar email de bienvenida a {profile_data['email']}")
                    print(f"   Nombre del cliente: {customer_name}")
                    print(f"   Email service configurado: {email_service.is_configured}")
                    
                    success, message = email_service.send_welcome_email(
                        profile_data['email'],
                        customer_name
                    )
                    
                    if success:
                        print(f"✅ Email de bienvenida enviado a {profile_data['email']}")
                        print(f"   Mensaje: {message}")
                    else:
                        print(f"⚠️  Error enviando email de bienvenida: {message}")
                        
                except Exception as e:
                    print(f"⚠️  Error en envío de email de bienvenida: {e}")
                    print(f"   Tipo de error: {type(e).__name__}")
                    # No fallar el registro por error de email
            
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/auth/login", methods=["POST"])
@require_csrf
def auth_login():
    """Endpoint para login de usuarios con rate limiting"""
    print(f"DEBUG: Iniciando proceso de login")
    
    if not AUTH_AVAILABLE:
        print(f"DEBUG: Sistema de autenticación no disponible")
        return jsonify({"error": "Sistema de autenticación no disponible"}), 503
    
    try:
        # Rate limiting mejorado
        client_ip = request.remote_addr
        rate_limits = get_rate_limits()
        print(f"DEBUG: IP del cliente: {client_ip}")
        
        if not check_rate_limit(client_ip, 'login', limit=rate_limits['login'], window=300):
            print(f"DEBUG: Rate limit excedido para IP: {client_ip}")
            return jsonify({"error": "Demasiados intentos de login. Intenta en 5 minutos."}), 429
        
        data = request.get_json()
        print(f"DEBUG: Datos recibidos: {data}")
        
        username = sanitize_input(data.get('username', ''))
        password = data.get('password', '')
        
        print(f"DEBUG: Usuario sanitizado: '{username}', Contraseña: {'*' * len(password)}")
        
        if not username or not password:
            print(f"DEBUG: Usuario o contraseña vacíos")
            return jsonify({"error": "Usuario y contraseña requeridos"}), 400
        
        # Validar longitud mínima
        if len(username) < 3 or len(password) < 6:
            print(f"DEBUG: Longitud insuficiente - Usuario: {len(username)}, Contraseña: {len(password)}")
            return jsonify({"error": "Usuario y contraseña deben tener al menos 3 y 6 caracteres respectivamente"}), 400
        
        print(f"DEBUG: Llamando a auth_manager.login con: {username}")
        result = auth_manager.login(username, password)
        print(f"DEBUG: Resultado del login: {result}")
        
        status_code = 200 if result['success'] else 401
        print(f"DEBUG: Retornando status code: {status_code}")
        
        return jsonify(result), status_code
        
    except Exception as e:
        print(f"DEBUG: Error en auth_login: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Error interno del servidor"}), 500

@app.route("/api/auth/logout", methods=["POST"])
@require_auth
@require_csrf
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
        
        # Validar campos requeridos (solo los editables)
        required_fields = ['telefono', 'email']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Campo {field} es requerido"}), 400
        
        # Validar formato de email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data['email']):
            return jsonify({"error": "Formato de email inválido"}), 400
        
        # DNI no se valida aquí ya que no es editable
        
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
            rows = execute_query(conn, "SELECT id, name, brand, price, COALESCE(porcentaje_descuento, NULL) as porcentaje_descuento, category, condition, sizes, stock, image, images, status, created_at, updated_at FROM productos ORDER BY id DESC").fetchall()
            return jsonify([row_to_dict(r) for r in rows]), 200
        finally:
            conn.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------- RUTAS DE DEBUG ----------------------

@app.route("/api/debug/sessions", methods=["GET"])
@debug_only
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
@debug_only
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
@debug_only
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
@debug_only
def create_test_users():
    """Debug: Crear usuarios de prueba"""
    try:
        # Primero eliminar usuarios existentes
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username IN ('admin', 'usuario')")
        conn.commit()
        conn.close()
        
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

@app.route("/api/debug/check-password", methods=["POST"])
@debug_only
def debug_check_password():
    """Debug: Verificar contraseña de un usuario"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"error": "Username y password requeridos"}), 400
        
        conn = get_conn()
        cursor = conn.cursor()
        
        # Obtener el hash de la contraseña del usuario
        cursor.execute(
            "SELECT id, username, password_hash, role FROM users WHERE username = %s",
            (username,)
        )
        user = cursor.fetchone()
        
        if user:
            password_hash = user[2]
            is_valid = auth_manager.verify_password(password, password_hash)
            
            return jsonify({
                "username": username,
                "password_hash": password_hash,
                "is_valid": is_valid,
                "user_id": user[0],
                "role": user[3]
            }), 200
        else:
            return jsonify({"error": "Usuario no encontrado"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route("/api/debug/user-hash/<username>", methods=["GET"])
@debug_only
def debug_user_hash(username):
    """Debug: Ver el hash de contraseña de un usuario"""
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, username, password_hash, role, nombre, apellido, email FROM users WHERE username = %s",
            (username,)
        )
        user = cursor.fetchone()
        
        if user:
            return jsonify({
                "id": user[0],
                "username": user[1],
                "password_hash": user[2],
                "role": user[3],
                "nombre": user[4],
                "apellido": user[5],
                "email": user[6]
            }), 200
        else:
            return jsonify({"error": "Usuario no encontrado"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route("/api/debug/test-hash", methods=["POST"])
@debug_only
def debug_test_hash():
    """Debug: Probar hash de contraseña"""
    try:
        data = request.get_json()
        password = data.get('password', 'admin123')
        
        # Generar hash de la contraseña
        import hashlib
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Verificar con el hash del usuario admin
        admin_hash = "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"
        
        return jsonify({
            "password": password,
            "generated_hash": password_hash,
            "admin_hash": admin_hash,
            "matches": password_hash == admin_hash
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------- RUTAS DE PAGOS ----------------------

@app.route("/api/payment/create-preference", methods=["POST"])
@require_csrf
def create_payment_preference():
    """Crear preferencia de pago en MercadoPago con rate limiting"""
    if not PAYMENT_AVAILABLE:
        return jsonify({"error": "Sistema de pagos no disponible"}), 503
    
    # Rate limiting para pagos
    client_ip = request.remote_addr
    rate_limits = get_rate_limits()
    
    if not check_rate_limit(client_ip, 'payment', limit=rate_limits['payment'], window=300):
        return jsonify({"error": "Demasiados intentos de pago. Intenta en 5 minutos."}), 429
    
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
        
        # Crear preferencia de pago (esto también crea el pedido en la BD)
        preference_result = payment_handler.create_payment_preference(items, customer_info)
        
        if preference_result['success']:
            return jsonify({
                "success": True,
                "preference_id": preference_result['preference_id'],
                "init_point": preference_result['init_point'],
                "sandbox_init_point": preference_result['sandbox_init_point'],
                "order_id": preference_result['order_id'],
                "total_amount": preference_result['total_amount']
            }), 200
        else:
            return jsonify(preference_result), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/payment/create-transfer-order", methods=["POST"])
@require_csrf
def create_transfer_order():
    """Crear pedido para pago por transferencia/depósito con rate limiting"""
    # Las transferencias siempre están disponibles, no dependen de MercadoPago
    
    # Rate limiting para transferencias
    client_ip = request.remote_addr
    rate_limits = get_rate_limits()
    
    if not check_rate_limit(client_ip, 'payment', limit=rate_limits['payment'], window=300):
        return jsonify({"error": "Demasiados intentos de pago. Intenta en 5 minutos."}), 429
    
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
        total_amount = data.get('total_amount', 0)
        
        print(f"DEBUG - Datos recibidos: {data}")
        print(f"DEBUG - Items: {items}")
        print(f"DEBUG - Total amount: {total_amount}")
        
        if not items:
            return jsonify({"error": "No hay items en el carrito"}), 400
        
        # Si el total_amount es 0, calcularlo desde los items
        if total_amount <= 0:
            total_amount = sum(item.get('price', 0) * item.get('quantity', 1) for item in items)
            print(f"DEBUG - Total recalculado: {total_amount}")
        
        if total_amount <= 0:
            return jsonify({"error": "Monto total inválido"}), 400
        
        # Agregar información del usuario
        customer_info['user_id'] = user['user_id']
        customer_info['user_email'] = user.get('email', '')
        
        # Usar payment_handler si está disponible, sino manejar directamente
        if PAYMENT_AVAILABLE:
            return payment_handler.create_transfer_order(items, customer_info, total_amount)
        else:
            # Manejar transferencia directamente sin payment_handler
            return create_transfer_order_direct(items, customer_info, total_amount)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def create_transfer_order_direct(items, customer_info, total_amount):
    """Crear pedido de transferencia directamente sin payment_handler"""
    try:
        from database import get_conn
        from datetime import datetime
        
        print(f"DEBUG - create_transfer_order_direct: items={items}, customer_info={customer_info}, total_amount={total_amount}")
        
        with get_conn() as conn:
            cursor = conn.cursor()
            
            # Crear número de pedido único
            order_number = f"TRF-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            print(f"DEBUG - order_number: {order_number}")
            
            # Generar código de verificación único
            import hashlib
            timestamp = datetime.now().timestamp()
            verification_code = hashlib.md5(f"{order_number}{timestamp}".encode()).hexdigest()[:8].upper()
            print(f"DEBUG - verification_code: {verification_code}")
            
            # Insertar pedido
            insert_params = (
                order_number,
                customer_info.get('name', ''),
                customer_info.get('email', ''),
                customer_info.get('phone', ''),
                customer_info.get('address', ''),
                customer_info.get('city', ''),
                customer_info.get('zip', ''),
                total_amount,
                'transfer',
                'pending_transfer'
            )
            print(f"DEBUG - Parámetros de inserción: {insert_params}")
            
            cursor.execute(
                """
                INSERT INTO orders (order_number, customer_name, customer_email, customer_phone, 
                                  customer_address, customer_city, customer_zip, total_amount, 
                                  payment_method, status, verification_code)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                insert_params + (verification_code,)
            )
            
            result = cursor.fetchone()
            print(f"DEBUG - cursor.fetchone() result: {result}")
            
            if result:
                # PostgreSQL devuelve RealDictRow, acceder por nombre de columna
                order_id = result['id']
                print(f"DEBUG - order_id obtenido: {order_id}")
            else:
                print("ERROR - No se pudo obtener el order_id")
                raise Exception("No se pudo obtener el ID del pedido")
            
            # Insertar items del pedido
            for item in items:
                print(f"DEBUG - Insertando item: {item}")
                
                # Obtener stock actual del producto
                cursor.execute(
                    "SELECT stock FROM productos WHERE id = %s",
                    (item['product_id'],)
                )
                product = cursor.fetchone()
                current_stock = int(product['stock']) if product else 0
                
                # Verificar stock disponible
                if current_stock < item['quantity']:
                    raise Exception(f"Stock insuficiente para el producto {item['product_id']}. Disponible: {current_stock}, Solicitado: {item['quantity']}")
                
                # Descontar stock
                new_stock = current_stock - item['quantity']
                cursor.execute(
                    "UPDATE productos SET stock = %s WHERE id = %s",
                    (new_stock, item['product_id'])
                )
                
                cursor.execute(
                    """
                    INSERT INTO order_items (order_id, product_id, quantity, price)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (order_id, item['product_id'], item['quantity'], item['price'])
                )
            
            conn.commit()
            print(f"DEBUG - Pedido guardado exitosamente con ID: {order_id}")
            
            # Enviar email de confirmación si está disponible
            if EMAIL_AVAILABLE and customer_info.get('email'):
                try:
                    # Preparar datos del pedido para el email
                    order_data = {
                        'order_number': order_number,
                        'created_at': datetime.now().strftime('%d/%m/%Y %H:%M'),
                        'status': 'Pendiente',
                        'payment_method': 'Transferencia',
                        'total_amount': total_amount,
                        'items': items
                    }
                    
                    # Enviar email de confirmación
                    success, message = email_service.send_order_confirmation(
                        customer_info['email'],
                        customer_info.get('name', 'Cliente'),
                        order_data
                    )
                    
                    if success:
                        print(f"✅ Email de confirmación enviado a {customer_info['email']}")
                    else:
                        print(f"⚠️  Error enviando email: {message}")
                        
                except Exception as e:
                    print(f"⚠️  Error en envío de email: {e}")
                    # No fallar el pedido por error de email
            
            return jsonify({
                "success": True,
                "order_id": order_id,
                "order_number": order_number,
                "verification_code": verification_code,
                "total_amount": total_amount,
                "message": "¡Pedido creado exitosamente! Realiza la transferencia a la cuenta de Jose Ignacio Abalo (MercadoPago) y envía el comprobante por WhatsApp al +54 295 454-4001"
            }), 200
            
    except Exception as e:
        print(f"Error al crear pedido de transferencia: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Error al crear pedido: {str(e)}"}), 500

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
    # Verificar autenticación
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Token de autenticación requerido"}), 401
    
    token = auth_header.split(' ')[1]
    user = auth_manager.validate_session(token)
    if not user:
        return jsonify({"error": "Sesión inválida"}), 401
    
    try:
        conn = get_conn()
        try:
            cursor = conn.cursor()
            
            # Obtener pedidos del usuario por user_id o email
            cursor.execute("""
                SELECT o.id, o.order_number, o.customer_name, o.customer_email, 
                       o.customer_phone, o.total_amount, o.payment_method, o.status,
                       o.created_at, o.updated_at, o.customer_address, o.customer_city, o.customer_zip
                FROM orders o
                WHERE o.user_id = %s OR o.customer_email = %s
                ORDER BY o.created_at DESC
            """, (user['user_id'], user.get('email', '')))
            
            orders = cursor.fetchall()
            
            result = []
            for order in orders:
                # Obtener items de cada pedido
                cursor.execute("""
                    SELECT oi.product_id, oi.quantity, oi.price, p.name, p.brand
                    FROM order_items oi
                    LEFT JOIN productos p ON oi.product_id = p.id
                    WHERE oi.order_id = %s
                """, (order[0],))
                
                items = cursor.fetchall()
                
                result.append({
                    'id': order[0],
                    'order_number': order[1],
                    'customer_name': order[2],
                    'customer_email': order[3],
                    'customer_phone': order[4],
                    'total_amount': float(order[5]),
                    'payment_method': order[6],
                    'status': order[7],
                    'created_at': order[8].isoformat() if order[8] else None,
                    'updated_at': order[9].isoformat() if order[9] else None,
                    'customer_address': order[10],
                    'customer_city': order[11],
                    'customer_zip': order[12],
                    'verification_code': order[13],
                    'items': [
                        {
                            'product_id': item[0],
                            'quantity': item[1],
                            'price': float(item[2]),
                            'name': item[3] or 'Producto eliminado',
                            'brand': item[4] or 'N/A'
                        }
                        for item in items
                    ]
                })
            
            return jsonify({"success": True, "orders": result}), 200
            
        finally:
            conn.close()
            
    except Exception as e:
        print(f"Error en get_user_orders: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ---------------------- GESTIÓN DE PEDIDOS (ADMIN) ----------------------

@app.route("/api/admin/orders", methods=["GET"])
@require_admin
def get_all_orders():
    """Obtener todos los pedidos (solo admin)"""
    try:
        conn = get_conn()
        try:
            # Obtener pedidos con información básica
            cursor = conn.cursor()
            cursor.execute("""
                SELECT o.id, o.order_number, o.customer_name, o.customer_email, 
                       o.customer_phone, o.total_amount, o.payment_method, o.status,
                       o.created_at, o.updated_at, o.customer_address, o.customer_city, o.customer_zip,
                       o.verification_code
                FROM orders o
                ORDER BY o.created_at DESC
            """)
            
            orders = cursor.fetchall()
            
            result = []
            for order in orders:
                # Obtener items de cada pedido
                cursor.execute("""
                    SELECT oi.product_id, oi.quantity, oi.price, p.name, p.brand
                    FROM order_items oi
                    LEFT JOIN productos p ON oi.product_id = p.id
                    WHERE oi.order_id = %s
                """, (order[0],))
                
                items = cursor.fetchall()
                
                result.append({
                    'id': order[0],
                    'order_number': order[1],
                    'customer_name': order[2],
                    'customer_email': order[3],
                    'customer_phone': order[4],
                    'total_amount': float(order[5]),
                    'payment_method': order[6],
                    'status': order[7],
                    'created_at': order[8].isoformat() if order[8] else None,
                    'updated_at': order[9].isoformat() if order[9] else None,
                    'customer_address': order[10],
                    'customer_city': order[11],
                    'customer_zip': order[12],
                    'verification_code': order[13],
                    'items': [
                        {
                            'product_id': item[0],
                            'quantity': item[1],
                            'price': float(item[2]),
                            'name': item[3] or 'Producto eliminado',
                            'brand': item[4] or 'N/A'
                        }
                        for item in items
                    ]
                })
            
            return jsonify({"success": True, "orders": result}), 200
            
        finally:
            conn.close()
            
    except Exception as e:
        print(f"Error en get_all_orders: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/admin/orders/<int:order_id>", methods=["GET"])
@require_admin
def get_order_details(order_id):
    """Obtener detalles de un pedido específico (solo admin)"""
    try:
        conn = get_conn()
        try:
            cursor = conn.cursor()
            
            # Obtener información del pedido
            cursor.execute("""
                SELECT o.id, o.order_number, o.customer_name, o.customer_email, 
                       o.customer_phone, o.customer_address, o.customer_city, o.customer_zip,
                       o.total_amount, o.payment_method, o.status, o.payment_id,
                       o.created_at, o.updated_at, o.user_id
                FROM orders o
                WHERE o.id = %s
            """, (order_id,))
            
            order = cursor.fetchone()
            if not order:
                return jsonify({"error": "Pedido no encontrado"}), 404
            
            # Obtener items del pedido
            cursor.execute("""
                SELECT oi.product_id, oi.quantity, oi.price, p.name, p.brand, p.image
                FROM order_items oi
                LEFT JOIN productos p ON oi.product_id = p.id
                WHERE oi.order_id = %s
            """, (order_id,))
            
            items = cursor.fetchall()
            
            result = {
                'id': order[0],
                'order_number': order[1],
                'customer_name': order[2],
                'customer_email': order[3],
                'customer_phone': order[4],
                'customer_address': order[5],
                'customer_city': order[6],
                'customer_zip': order[7],
                'total_amount': float(order[8]),
                'payment_method': order[9],
                'status': order[10],
                'payment_id': order[11],
                'created_at': order[12].isoformat() if order[12] else None,
                'updated_at': order[13].isoformat() if order[13] else None,
                'user_id': order[14],
                'items': [
                    {
                        'product_id': item[0],
                        'quantity': item[1],
                        'price': float(item[2]),
                        'name': item[3] or 'Producto eliminado',
                        'brand': item[4] or 'N/A',
                        'image': item[5] or ''
                    }
                    for item in items
                ]
            }
            
            return jsonify({"success": True, "order": result}), 200
            
        finally:
            conn.close()
            
    except Exception as e:
        print(f"Error en get_order_details: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/admin/orders/<int:order_id>/status", methods=["PUT"])
@require_admin
def update_order_status(order_id):
    """Actualizar estado de un pedido (solo admin)"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({"error": "Estado requerido"}), 400
        
        # Validar estados permitidos
        valid_statuses = ['pending', 'pending_transfer', 'paid', 'shipped', 'delivered', 'cancelled']
        if new_status not in valid_statuses:
            return jsonify({"error": f"Estado inválido. Estados permitidos: {', '.join(valid_statuses)}"}), 400
        
        conn = get_conn()
        try:
            cursor = conn.cursor()
            
            # Verificar que el pedido existe
            cursor.execute("SELECT id FROM orders WHERE id = %s", (order_id,))
            if not cursor.fetchone():
                return jsonify({"error": "Pedido no encontrado"}), 404
            
            # Actualizar estado
            cursor.execute("""
                UPDATE orders 
                SET status = %s, updated_at = CURRENT_TIMESTAMP 
                WHERE id = %s
            """, (new_status, order_id))
            
            conn.commit()
            
            return jsonify({
                "success": True, 
                "message": f"Estado del pedido actualizado a: {new_status}"
            }), 200
            
        finally:
            conn.close()
            
    except Exception as e:
        print(f"Error en update_order_status: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/admin/orders/<int:order_id>", methods=["DELETE"])
@require_admin
def delete_order(order_id):
    """Eliminar un pedido (solo admin)"""
    try:
        conn = get_conn()
        try:
            cursor = conn.cursor()
            
            # Verificar que el pedido existe
            cursor.execute("SELECT id FROM orders WHERE id = %s", (order_id,))
            if not cursor.fetchone():
                return jsonify({"error": "Pedido no encontrado"}), 404
            
            # Eliminar items del pedido primero (por la foreign key)
            cursor.execute("DELETE FROM order_items WHERE order_id = %s", (order_id,))
            
            # Eliminar el pedido
            cursor.execute("DELETE FROM orders WHERE id = %s", (order_id,))
            conn.commit()
            
            return jsonify({"success": True, "message": "Pedido eliminado exitosamente"}), 200
        finally:
            conn.close()
    except Exception as e:
        print(f"Error en delete_order: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ---------------------- GESTIÓN DE USUARIOS (ADMIN) ----------------------

@app.route("/api/admin/users", methods=["GET"])
@require_admin
def get_all_users():
    """Obtener todos los usuarios (solo admin)"""
    try:
        print(f"DEBUG: Obteniendo lista de usuarios para admin")
        users = auth_manager.get_all_users()
        print(f"DEBUG: Usuarios obtenidos: {len(users)} usuarios")
        return jsonify({"success": True, "users": users}), 200
    except Exception as e:
        print(f"DEBUG: Error en get_all_users: {str(e)}")
        import traceback
        traceback.print_exc()
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
        if data.get('email'):
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, data['email']):
                return jsonify({"error": "Formato de email inválido"}), 400
        
        if data.get('dni'):
            if not data['dni'].isdigit() or len(data['dni']) != 8:
                return jsonify({"error": "DNI debe contener exactamente 8 números"}), 400
        
        if data.get('telefono'):
            if not data['telefono'].isdigit():
                return jsonify({"error": "Teléfono debe contener solo números"}), 400
        
        if data.get('codigo_postal'):
            if not data['codigo_postal'].isdigit() or len(data['codigo_postal']) < 4 or len(data['codigo_postal']) > 5:
                return jsonify({"error": "Código postal debe contener entre 4 y 5 números"}), 400
        
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
@require_csrf
def create_user_admin():
    """Crear un nuevo usuario (solo admin)"""
    try:
        data = request.get_json()
        
        # Validaciones requeridas
        if not data.get('username') or not data.get('password'):
            return jsonify({"error": "Username y password son requeridos"}), 400
        
        # Validar longitud de contraseña (mínimo 8 caracteres)
        if len(data['password']) < 8:
            return jsonify({"error": "La contraseña debe tener al menos 8 caracteres"}), 400
        
        # Validar que la contraseña contenga letras y números
        has_letter = any(c.isalpha() for c in data['password'])
        has_number = any(c.isdigit() for c in data['password'])
        if not (has_letter and has_number):
            return jsonify({"error": "La contraseña debe contener al menos una letra y un número"}), 400
        
        # Validar formato de email
        if data.get('email'):
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, data['email']):
                return jsonify({"error": "Formato de email inválido"}), 400
        
        # Validar DNI (exactamente 8 dígitos)
        if data.get('dni'):
            if not data['dni'].isdigit() or len(data['dni']) != 8:
                return jsonify({"error": "DNI debe contener exactamente 8 números"}), 400
        
        # Validar teléfono (solo números)
        if data.get('telefono'):
            if not data['telefono'].isdigit():
                return jsonify({"error": "Teléfono debe contener solo números"}), 400
        
        # Validar código postal (4 o 5 dígitos)
        if data.get('codigo_postal'):
            if not data['codigo_postal'].isdigit() or len(data['codigo_postal']) < 4 or len(data['codigo_postal']) > 5:
                return jsonify({"error": "Código postal debe contener entre 4 y 5 números"}), 400
        
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
    # Verificar configuración antes de iniciar
    from config import check_database_config, check_cloudinary_config, check_mercadopago_config
    
    print("🔍 Verificando configuración...")
    check_database_config()
    check_cloudinary_config()
    check_mercadopago_config()
    print("✅ Configuración verificada")
    
    init_db()
    
    # Configuración para Railway
    import os
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"🚀 Iniciando servidor en puerto {port} (debug={debug})")
    app.run(host="0.0.0.0", port=port, debug=debug)