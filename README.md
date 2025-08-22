# WHIP HELMETS - E-commerce Web Application

## 📁 Estructura de Archivos Reorganizada

```
whip-helmets/
├── index.html                          # Página principal
├── pages/                              # Páginas secundarias
│   ├── politica-de-privacidad.html     # Política de privacidad
│   └── terminos-y-condiciones.html     # Términos y condiciones
├── admin/                              # Panel de administración
│   ├── index.html                      # Dashboard administrativo
│   ├── login.html                      # Login del admin
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
│   ├── init_db.py                      # Inicialización de BD
│   ├── requirements.txt                # Dependencias Python
│   ├── README.txt                      # Documentación del backend
│   └── productos.db                    # Base de datos SQLite (generado)
└── README.md                           # Documentación principal
```

## 🚀 Instalación y Configuración

### Prerrequisitos
- Python 3.10+
- Navegador web moderno

### Pasos de instalación

1. **Clonar/Descargar el proyecto**
   ```bash
   git clone [url-del-repositorio]
   cd whip-helmets
   ```

2. **Configurar el Backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   python init_db.py  # Opcional: para recrear la BD
   python server.py
   ```
   
   El servidor iniciará en: `http://127.0.0.1:5000`

3. **Configurar las imágenes**
   - Colocar `logo.png` en `assets/images/`
   - Colocar `fondo1.jpg` en `assets/images/backgrounds/`
   - Las imágenes de productos van en `assets/images/products/`

4. **Acceder a la aplicación**
   - **Frontend**: Abrir `index.html` en el navegador
   - **Admin Panel**: Ir a `admin/login.html`
     - Usuario: `admin`
     - Contraseña: `admin`

## 🌟 Características

### Frontend Principal
- ✅ Catálogo de productos dinámico
- ✅ Carrito de compras con LocalStorage
- ✅ Control de stock en tiempo real
- ✅ Filtros por marca y categoría
- ✅ Diseño responsive
- ✅ Sistema de notificaciones

### Panel Administrativo
- ✅ CRUD completo de productos
- ✅ Gestión de stock
- ✅ Filtros avanzados
- ✅ Exportación de datos (CSV)
- ✅ Guardado masivo de cambios
- ✅ Autenticación básica

### Backend API
- ✅ REST API completa
- ✅ Base de datos SQLite
- ✅ Validación de datos
- ✅ Manejo de errores
- ✅ CORS configurado

## 📋 Endpoints de la API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/health` | Estado de la API |
| GET | `/api/products` | Listar productos |
| POST | `/api/products` | Crear producto |
| PUT | `/api/products/{id}` | Actualizar producto |
| DELETE | `/api/products/{id}` | Eliminar producto |
| POST | `/api/seed` | Datos de ejemplo |

## 🔧 Configuración

### Cambiar credenciales de admin
Editar en `admin/login.html`:
```javascript
if (username === 'admin' && password === 'admin') {
```

### Modificar URL de la API
Cambiar en `assets/js/shop.js` y `admin/js/admin.js`:
```javascript
const API_BASE = "http://127.0.0.1:5000";
```

### Personalizar productos
- Modificar los datos en `backend/server.py` (función `init_db`)
- O usar el panel administrativo

## 🎨 Personalización

### Colores principales
En `assets/css/style.css`:
```css
:root {
    --primary-color: #f0ad4e;  /* Dorado */
    --secondary-color: #000;    /* Negro */
    --dark-bg: #222;           /* Gris oscuro */
}
```

### Fuentes
Cambiar en `assets/css/style.css`:
```css
@import url('https://fonts.googleapis.com/css2?family=Bangers&display=swap');
```

## 📱 Responsive Design

La aplicación es completamente responsive con breakpoints en:
- **Desktop**: > 768px
- **Tablet**: 768px - 480px  
- **Mobile**: < 480px

## 🛡️ Seguridad

⚠️ **Para producción, implementar:**
- Autenticación JWT real
- Validación de entrada robusta
- HTTPS
- Rate limiting
- Sanitización de datos

## 🐛 Solución de Problemas

### Error "No se puede conectar al servidor"
- Verificar que el backend esté ejecutándose
- Comprobar la URL de la API
- Revisar la consola del navegador

### Las imágenes no cargan
- Verificar que las rutas en la base de datos coincidan con la estructura de archivos
- Comprobar que las imágenes existan en `assets/images/`

### El carrito no persiste
- Verificar que LocalStorage esté habilitado
- Comprobar permisos del navegador

## 🤝 Contribución

1. Fork del proyecto
2. Crear rama para feature (`git checkout -b feature/NuevaCaracteristica`)
3. Commit de cambios (`git commit -m 'Agregar nueva característica'`)
4. Push a la rama (`git push origin feature/NuevaCaracteristica`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo `LICENSE` para detalles.

## Soporte

Para soporte y consultas:
- Email: contacto@whip-helmets.com
- WhatsApp: +542954544001
- Instagram: @whip.helmets

---

**Desarrollado con ❤️ para WHIP HELMETS**