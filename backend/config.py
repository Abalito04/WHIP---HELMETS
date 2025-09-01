import os

# Configuración de MercadoPago
# Railway usará la variable de entorno MP_ACCESS_TOKEN
MP_ACCESS_TOKEN = os.environ.get('MP_ACCESS_TOKEN', 'TEST-123456789-123456789-123456789')

# URLs para Railway (se configuran automáticamente)
# Railway proporciona la URL en la variable PORT
PORT = int(os.environ.get('PORT', 5000))
BASE_URL = os.environ.get('RAILWAY_STATIC_URL', f"http://localhost:{PORT}")

# Si estás en Railway, usa la URL del dominio
if 'RAILWAY_STATIC_URL' in os.environ:
    BASE_URL = os.environ.get('RAILWAY_STATIC_URL')
elif 'RAILWAY_PUBLIC_DOMAIN' in os.environ:
    BASE_URL = f"https://{os.environ.get('RAILWAY_PUBLIC_DOMAIN')}"

SUCCESS_URL = f"{BASE_URL}/payment/success"
FAILURE_URL = f"{BASE_URL}/payment/failure"
PENDING_URL = f"{BASE_URL}/payment/pending"
WEBHOOK_URL = f"{BASE_URL}/api/payment/webhook"

# Configuración de la aplicación
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
SECRET_KEY = os.environ.get('SECRET_KEY', 'cambia-esta-clave-secreta-en-produccion')

# Configuración de la base de datos
DATABASE_PATH = os.environ.get('DATABASE_PATH', 'productos.db')
USERS_DATABASE_PATH = os.environ.get('USERS_DATABASE_PATH', 'users.db')
