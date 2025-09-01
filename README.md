# WHIP HELMETS - E-commerce Web Application

## 🚀 **ESTADO ACTUAL: OPERACIONAL EN RAILWAY**

### ✅ **FUNCIONALIDADES COMPLETADAS:**
- ✅ **Deploy en Railway** - Configuración completa
- ✅ **Base de datos** - Creación automática con datos de ejemplo
- ✅ **Autenticación** - Sistema de login/logout con rate limiting
- ✅ **Productos** - CRUD completo con filtros avanzados
- ✅ **Carrito** - Funcionalidad completa con persistencia
- ✅ **Responsive** - Optimizado para móviles, tablets y desktop
- ✅ **Admin panel** - Gestión completa de productos y usuarios
- ✅ **Checkout** - Integración con MercadoPago
- ✅ **Seguridad básica** - Rate limiting, sanitización de inputs
- ✅ **Optimización de imágenes** - Procesamiento automático

### 🔧 **CONFIGURACIÓN REQUERIDA EN RAILWAY:**

#### **Variables de Entorno Obligatorias:**
```bash
# MercadoPago (CRÍTICO para pagos)
MP_ACCESS_TOKEN=tu_access_token_real_aqui

# Seguridad
SECRET_KEY=tu_clave_secreta_unica_aqui
JWT_SECRET_KEY=tu_jwt_secret_key_aqui

# Configuración
DEBUG=False
IS_PRODUCTION=True
```

#### **Variables de Entorno Opcionales:**
```bash
# Rate limiting
RATE_LIMIT_PER_MINUTE=60

# JWT
JWT_ACCESS_TOKEN_EXPIRES=3600

# Email (para futuras implementaciones)
SMTP_SERVER=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
```

### 👥 **USUARIOS POR DEFECTO:**
- **Admin:** `admin` / `admin123`
- **Usuario:** `usuario` / `user123`

## 📁 Estructura de Archivos Reorganizada

```
whip-helmets/
├── index.html                          # Página principal
├── pages/                              # Páginas secundarias
│   ├── politica-de-privacidad.html     # Política de privacidad
│   └── terminos-y-condiciones.html     # Términos y condiciones
├── admin/                              # Panel de administración
│   ├── admin.html                      # Dashboard administrativo
│   ├── css/
│   │   └── admin.css                   # Estilos del panel admin
│   └── js/
│       └── admin.js                    # Lógica del panel admin
├── assets/                             # Recursos del frontend
│   ├── css/
│   │   └── style.css                   # Estilos principales
│   ├── js/
│   │   ├── script.js                   # Funciones de carrito y UI
│   │   └── shop.js                     # Comunicación con API
│   └── images/                         # Imágenes organizadas
│       ├── logo.png                    # Logo principal
│       ├── backgrounds/
│       │   └── fondo1.jpg              # Imagen de fondo hero
│       └── products/                   # Imágenes de productos
├── backend/                            # Servidor y API
│   ├── server.py                       # Servidor Flask principal
│   ├── auth.py                         # Sistema de autenticación
│   ├── payment_handler.py              # Integración MercadoPago
│   ├── image_processor.py              # Optimización de imágenes
│   ├── config.py                       # Configuración
│   ├── requirements.txt                # Dependencias Python
│   └── productos.db                    # Base de datos SQLite (generado)
├── payment/                            # Páginas de pago
│   ├── success.html                    # Pago exitoso
│   ├── failure.html                    # Pago fallido
│   └── pending.html                    # Pago pendiente
├── app.py                              # Entry point para Railway
├── Procfile                            # Comando de inicio
├── runtime.txt                         # Versión de Python
└── requirements.txt                    # Dependencias (raíz)
```

## 🚀 Instalación y Configuración

### ☁️ Despliegue en Railway (Recomendado)

**📋 Ver `RAILWAY_DEPLOY.md` para instrucciones detalladas**

1. **Subir a GitHub** (con todos los archivos)
2. **Conectar Railway** con tu repositorio
3. **Configurar variables de entorno** en Railway
4. **¡Listo!** La app estará online

### 🖥️ Desarrollo Local

#### Prerrequisitos
- Python 3.10+
- Navegador web moderno

#### Pasos de instalación

1. **Clonar/Descargar el proyecto**
   ```bash
   git clone [url-del-repositorio]
   cd whip-helmets
   ```

2. **Configurar el Backend**
   ```bash
   cd backend
   
   # Configurar archivo de configuración
   cp config.example.py config.py
   # EDITAR config.py con tus credenciales de MercadoPago
   
   pip install -r requirements.txt
   python server.py  # Las bases de datos se crean automáticamente
   ```
   
   El servidor iniciará en: `http://127.0.0.1:5000`

## 🌟 Características

### Frontend Principal
- ✅ Catálogo de productos dinámico
- ✅ Carrito de compras con LocalStorage
- ✅ Control de stock en tiempo real
- ✅ Filtros por marca y categoría
- ✅ Diseño responsive completo
- ✅ Sistema de notificaciones
- ✅ Galería de imágenes de productos

### Panel Administrativo
- ✅ CRUD completo de productos
- ✅ Gestión de stock
- ✅ Filtros avanzados
- ✅ Exportación de datos (CSV)
- ✅ Guardado masivo de cambios
- ✅ Autenticación segura
- ✅ Gestión de usuarios
- ✅ Optimización de imágenes
- ✅ Estadísticas de productos

### Backend API
- ✅ REST API completa
- ✅ Base de datos SQLite
- ✅ Validación de datos robusta
- ✅ Manejo de errores
- ✅ CORS configurado
- ✅ Rate limiting
- ✅ Sanitización de inputs
- ✅ Integración MercadoPago

### Seguridad
- ✅ Rate limiting en login
- ✅ Sanitización de inputs
- ✅ Validación de datos
- ✅ Manejo seguro de errores
- ✅ Autenticación con tokens

## 📋 Endpoints de la API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/health` | Estado de la API |
| GET | `/api/products` | Listar productos |
| POST | `/api/products` | Crear producto |
| PUT | `/api/products/{id}` | Actualizar producto |
| DELETE | `/api/products/{id}` | Eliminar producto |
| POST | `/api/auth/login` | Login de usuario |
| POST | `/api/auth/logout` | Logout de usuario |
| GET | `/api/profile` | Obtener perfil |
| PUT | `/api/profile` | Actualizar perfil |
| POST | `/api/payment/create-preference` | Crear preferencia de pago |
| POST | `/api/payment/webhook` | Webhook de MercadoPago |
| GET | `/api/orders` | Obtener pedidos del usuario |

## 🛡️ Seguridad Implementada

✅ **Rate Limiting** - Máximo 5 intentos de login por 5 minutos
✅ **Sanitización** - Limpieza de inputs del usuario
✅ **Validación** - Verificación de datos de entrada
✅ **Manejo de errores** - Respuestas seguras sin información sensible
✅ **Autenticación** - Sistema de tokens con expiración

## 🚨 **MEJORAS FUTURAS RECOMENDADAS:**

### 🔐 **Seguridad Avanzada (Prioridad Alta)**
- [ ] Implementar JWT real con refresh tokens
- [ ] Agregar validación de contraseñas robusta
- [ ] Implementar 2FA para administradores
- [ ] Agregar logging de seguridad

### 💳 **Pagos (Prioridad Alta)**
- [ ] Probar flujo completo de pagos en producción
- [ ] Implementar manejo de webhooks de MercadoPago
- [ ] Agregar notificaciones de pago por email
- [ ] Implementar reembolsos

### 📧 **Notificaciones (Prioridad Media)**
- [ ] Email de confirmación de pedidos
- [ ] Notificaciones de stock bajo
- [ ] Email de bienvenida para nuevos usuarios
- [ ] Notificaciones de estado de pedido

### 📊 **Analytics (Prioridad Media)**
- [ ] Tracking de ventas
- [ ] Estadísticas de productos más vendidos
- [ ] Reportes de inventario
- [ ] Dashboard de métricas

### 🔍 **SEO (Prioridad Baja)**
- [ ] Meta tags para SEO
- [ ] Open Graph tags
- [ ] Schema.org markup
- [ ] Sitemap.xml

## 🐛 Solución de Problemas

### Error "No se puede conectar al servidor"
- Verificar que el backend esté ejecutándose
- Comprobar la URL de la API
- Revisar la consola del navegador

### Las imágenes no cargan
- Verificar que las imágenes estén en el repositorio
- Comprobar las rutas en la base de datos
- Revisar permisos de archivos

### Error de autenticación
- Verificar credenciales de usuario
- Comprobar que la base de datos esté creada
- Revisar logs del servidor

### Error de pagos
- Verificar credenciales de MercadoPago
- Comprobar configuración de URLs
- Revisar webhooks

## 📞 Soporte

Para problemas técnicos:
1. Revisa los logs en Railway
2. Verifica las variables de entorno
3. Comprueba que todas las dependencias estén en `requirements.txt`
4. Consulta la documentación en `RAILWAY_DEPLOY.md`