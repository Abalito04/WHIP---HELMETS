# 🔧 Configuración del Backend

## 📋 Pasos de Configuración

### 1. Configurar el archivo de configuración

**IMPORTANTE**: El archivo `config.py` contiene datos sensibles y NO se sube a GitHub.

Para configurar el proyecto:

1. **Copiar el archivo de ejemplo:**
   ```bash
   cp config.example.py config.py
   ```

2. **Editar `config.py` con tus credenciales reales:**
   ```python
   # Reemplaza con tu Access Token real de MercadoPago
   MP_ACCESS_TOKEN = "TU_ACCESS_TOKEN_REAL_AQUI"
   
   # Cambia la clave secreta en producción
   SECRET_KEY = "tu-clave-secreta-unica-aqui"
   ```

### 2. Obtener credenciales de MercadoPago

1. Ve a [MercadoPago Developers](https://www.mercadopago.com.ar/developers/panel/credentials)
2. Crea una cuenta o inicia sesión
3. Ve a "Credenciales" en el panel
4. Copia tu **Access Token** (para pruebas usa el de "Test")

### 3. Inicializar las bases de datos

```bash
# Crear base de datos de productos
python init_db.py

# Crear base de datos de usuarios
python init_users_db.py
```

### 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 5. Ejecutar el servidor

```bash
python server.py
```

El servidor estará disponible en: `http://127.0.0.1:5000`

## 🔐 Credenciales por Defecto

Después de ejecutar `init_users_db.py`, se crean estos usuarios:

- **Administrador**: `admin` / `admin123`
- **Usuario normal**: `usuario` / `user123`

## ⚠️ Seguridad

- **NUNCA** subas `config.py` a GitHub
- **NUNCA** compartas tus credenciales de MercadoPago
- Cambia las contraseñas por defecto en producción
- Usa variables de entorno en producción

## 🚀 Variables de Entorno (Recomendado)

Para mayor seguridad, puedes usar variables de entorno:

```bash
# En Windows (PowerShell)
$env:MP_ACCESS_TOKEN="tu-token-aqui"

# En Linux/Mac
export MP_ACCESS_TOKEN="tu-token-aqui"
```

Y en `config.py`:
```python
MP_ACCESS_TOKEN = os.environ.get('MP_ACCESS_TOKEN', 'token-por-defecto')
```
