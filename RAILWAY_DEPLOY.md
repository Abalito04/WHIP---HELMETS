# 🚀 Despliegue en Railway

## 📋 Pasos para desplegar en Railway

### 1. Preparar el repositorio

Asegúrate de que tu repositorio contenga:
- ✅ `Procfile` (comando de inicio)
- ✅ `runtime.txt` (versión de Python)
- ✅ `app.py` (archivo principal para Railway)
- ✅ `requirements.txt` (dependencias en la raíz)
- ✅ `backend/config.py` (configurado para variables de entorno)
- ✅ `backend/requirements.txt` (dependencias del backend)

### 2. Conectar con Railway

1. Ve a [Railway.app](https://railway.app)
2. Inicia sesión con tu cuenta de GitHub
3. Haz clic en "New Project"
4. Selecciona "Deploy from GitHub repo"
5. Selecciona tu repositorio

### 3. Configurar Base de Datos PostgreSQL

**Paso 3a: Agregar base de datos PostgreSQL**
1. En tu proyecto de Railway, haz clic en **"New"**
2. Selecciona **"Database"** → **"PostgreSQL"**
3. Railway creará automáticamente la variable `DATABASE_URL`
4. Espera a que la base de datos esté lista (aparecerá como "Deployed")

### 4. Configurar Variables de Entorno

En Railway, ve a la pestaña "Variables" y agrega:

```bash
# Credenciales de MercadoPago
MP_ACCESS_TOKEN=tu_access_token_real_aqui

# Configuración de la aplicación
SECRET_KEY=tu_clave_secreta_unica_aqui
DEBUG=False

# Credenciales de Cloudinary (para subida de imágenes)
CLOUDINARY_CLOUD_NAME=ddowcuhlu
CLOUDINARY_API_KEY=291494695985798
CLOUDINARY_API_SECRET=pSrCsNF60-t5bSP_YUA2iGrTvBA

# O alternativamente, usar la URL completa:
# CLOUDINARY_URL=cloudinary://291494695985798:pSrCsNF60-t5bSP_YUA2iGrTvBA@ddowcuhlu

# Configuración de PostgreSQL (Railway proporciona DATABASE_URL automáticamente)
# Si usas una base de datos externa, configura estas variables:
# PGHOST=tu-host-postgresql
# PGPORT=5432
# PGDATABASE=whip_helmets
# PGUSER=tu-usuario
# PGPASSWORD=tu-password

# Forzar uso de PostgreSQL (recomendado para producción)
FORCE_POSTGRESQL=true

# URLs (Railway las configura automáticamente)
RAILWAY_STATIC_URL=https://tu-app.railway.app
```

### 5. Obtener credenciales de MercadoPago

1. Ve a [MercadoPago Developers](https://www.mercadopago.com.ar/developers/panel/credentials)
2. Crea una cuenta o inicia sesión
3. Ve a "Credenciales" en el panel
4. Copia tu **Access Token** (usa el de "Production" para producción)

### 6. Configurar Cloudinary (para subida de imágenes)

1. Ve a [Cloudinary Console](https://cloudinary.com/console)
2. Crea una cuenta gratuita (25GB gratis)
3. En el Dashboard, copia:
   - **Cloud Name**
   - **API Key**
   - **API Secret**
4. Agrega estas credenciales en Railway como variables de entorno

**Beneficios de Cloudinary:**
- ✅ **25GB gratis** para siempre
- ✅ **URLs permanentes** - Las imágenes nunca se pierden
- ✅ **Optimización automática** - Redimensiona y comprime imágenes
- ✅ **CDN global** - Carga rápida desde cualquier lugar

### 6. Configurar el dominio personalizado (opcional)

1. En Railway, ve a "Settings"
2. En "Domains", agrega tu dominio personalizado
3. Configura los registros DNS según las instrucciones

### 6. Verificar el despliegue

1. Railway automáticamente detectará que es una aplicación Python
2. Usará el `Procfile` para iniciar la aplicación
3. El healthcheck verificará `/api/health`
4. La aplicación estará disponible en la URL de Railway

## 🔧 Configuración Automática

Railway automáticamente:
- ✅ Detecta que es una aplicación Python
- ✅ Instala las dependencias de `requirements.txt`
- ✅ Ejecuta el comando del `Procfile`
- ✅ Configura el puerto y dominio
- ✅ Proporciona variables de entorno
- ✅ Crea las bases de datos al iniciar la aplicación
- ✅ Inserta usuarios y productos por defecto

## 🛡️ Seguridad en Producción

- ✅ Las credenciales están en variables de entorno
- ✅ `DEBUG=False` en producción
- ✅ `SECRET_KEY` única y segura
- ✅ HTTPS automático en Railway

## 📊 Monitoreo

Railway proporciona:
- ✅ Logs en tiempo real
- ✅ Métricas de rendimiento
- ✅ Alertas automáticas
- ✅ Rollback fácil

## 🔄 Actualizaciones

Para actualizar:
1. Haz push a tu repositorio
2. Railway automáticamente redeploya
3. No hay tiempo de inactividad

## 🐛 Solución de Problemas

### Error de puerto
- Railway configura automáticamente el puerto
- El código ya está preparado para usar `PORT`

### Error "python: command not found"
- ✅ Se solucionó con `app.py` en la raíz del proyecto
- ✅ Se simplificó la configuración eliminando archivos complejos
- ✅ Se agregó `requirements.txt` en la raíz
- ✅ Se agregó `runtime.txt` para especificar la versión de Python

### Error de base de datos
- ✅ Las bases de datos se crean automáticamente al iniciar la aplicación
- ✅ Los usuarios por defecto se crean automáticamente:
  - **admin / admin123** (rol: admin)
  - **usuario / user123** (rol: user)
- ✅ Los productos de ejemplo se insertan automáticamente

### Error de imágenes
- Las imágenes deben estar en el repositorio
- Las rutas son relativas al directorio del proyecto

## 📞 Soporte

Si tienes problemas:
1. Revisa los logs en Railway
2. Verifica las variables de entorno
3. Comprueba que todas las dependencias estén en `requirements.txt`
