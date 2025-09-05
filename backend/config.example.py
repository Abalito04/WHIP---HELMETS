import os

# Configuración de MercadoPago
# IMPORTANTE: Reemplaza con tus credenciales reales de MercadoPago
# Obtén tus credenciales en: https://www.mercadopago.com.ar/developers/panel/credentials
MP_ACCESS_TOKEN = os.environ.get('MP_ACCESS_TOKEN', 'TU_ACCESS_TOKEN_AQUI')

# URLs de desarrollo (cambiar en producción)
BASE_URL = "http://127.0.0.1:5000"
SUCCESS_URL = f"{BASE_URL}/payment/success"
FAILURE_URL = f"{BASE_URL}/payment/failure"
PENDING_URL = f"{BASE_URL}/payment/pending"
WEBHOOK_URL = f"{BASE_URL}/api/payment/webhook"

# Configuración de la aplicación
DEBUG = True
# IMPORTANTE: Cambia esta clave secreta en producción
SECRET_KEY = "cambia-esta-clave-secreta-en-produccion"

# Configuración de la base de datos
DATABASE_PATH = "productos.db"
USERS_DATABASE_PATH = "users.db"

# Configuración de Cloudinary
# IMPORTANTE: Obtén tus credenciales en: https://cloudinary.com/console
CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME', 'tu_cloud_name_aqui')
CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY', 'tu_api_key_aqui')
CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET', 'tu_api_secret_aqui')
