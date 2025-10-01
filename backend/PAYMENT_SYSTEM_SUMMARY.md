# Sistema de Pedidos - Resumen Completo

## 🎯 **Objetivo**
El sistema almacena **TODOS los tipos de pago** en la base de datos, permitiendo un seguimiento completo de pedidos desde el panel admin.

## 📊 **Tipos de Pago Soportados**

### 1. **Transferencia/Depósito**
- **Endpoint:** `/api/payment/create-transfer-order`
- **Método:** `transfer`
- **Estado inicial:** `pending_transfer`
- **Precio:** Precio efectivo (con descuento)
- **Datos bancarios:** Se muestran al usuario

### 2. **MercadoPago**
- **Endpoint:** `/api/payment/create-preference`
- **Método:** `mercadopago`
- **Estado inicial:** `pending`
- **Precio:** Precio de lista (sin descuento)
- **Integración:** Webhook para actualizar estados

## 🗄️ **Estructura de Base de Datos**

### Tabla `orders`
```sql
- id (SERIAL PRIMARY KEY)
- order_number (VARCHAR) - Número único del pedido
- customer_name (VARCHAR) - Nombre del cliente
- customer_email (VARCHAR) - Email del cliente
- customer_phone (VARCHAR) - Teléfono del cliente
- customer_address (TEXT) - Dirección del cliente
- customer_city (VARCHAR) - Ciudad del cliente
- customer_zip (VARCHAR) - Código postal
- total_amount (DECIMAL) - Monto total del pedido
- payment_method (VARCHAR) - 'transfer' o 'mercadopago'
- payment_id (VARCHAR) - ID de pago (MercadoPago)
- status (VARCHAR) - Estado del pedido
- user_id (INTEGER) - ID del usuario (opcional)
- created_at (TIMESTAMP) - Fecha de creación
- updated_at (TIMESTAMP) - Fecha de actualización
```

### Tabla `order_items`
```sql
- id (SERIAL PRIMARY KEY)
- order_id (INTEGER) - Referencia al pedido
- product_id (INTEGER) - ID del producto
- quantity (INTEGER) - Cantidad
- price (DECIMAL) - Precio unitario
- created_at (TIMESTAMP) - Fecha de creación
```

## 🔄 **Estados de Pedidos**

| Estado | Descripción | Aplicable a |
|--------|-------------|-------------|
| `pending` | Pendiente de pago | MercadoPago |
| `pending_transfer` | Pendiente transferencia | Transferencia |
| `paid` | Pagado | Ambos |
| `shipped` | Enviado | Ambos |
| `delivered` | Entregado | Ambos |
| `cancelled` | Cancelado | Ambos |

## 🎛️ **Panel Admin**

### Funcionalidades
- ✅ **Ver todos los pedidos** (ambos tipos de pago)
- ✅ **Filtrar por método de pago** (Transferencia/MercadoPago)
- ✅ **Filtrar por estado**
- ✅ **Buscar por número, cliente o email**
- ✅ **Ver detalles completos** del pedido
- ✅ **Actualizar estado** del pedido
- ✅ **Paginación** para manejar muchos pedidos

### Endpoints Admin
- `GET /api/admin/orders` - Listar todos los pedidos
- `GET /api/admin/orders/<id>` - Ver detalles de un pedido
- `PUT /api/admin/orders/<id>/status` - Actualizar estado

## 👤 **Panel Usuario**

### Funcionalidades
- ✅ **Ver mis pedidos** (solo los del usuario autenticado)
- ✅ **Ver detalles** de cada pedido
- ✅ **Seguimiento del estado**

### Endpoints Usuario
- `GET /api/orders` - Listar pedidos del usuario

## 🔧 **Flujo de Pedidos**

### Transferencia
1. Usuario selecciona "Transferencia/Depósito"
2. Se crea pedido con estado `pending_transfer`
3. Se muestran datos bancarios
4. Usuario realiza transferencia
5. Admin actualiza estado a `paid` cuando confirma pago

### MercadoPago
1. Usuario selecciona "MercadoPago"
2. Se crea pedido con estado `pending`
3. Se redirige a MercadoPago
4. Webhook actualiza estado automáticamente
5. Admin puede ver y gestionar el pedido

## 📱 **Integración Frontend**

### Checkout
- ✅ **Selector de método de pago**
- ✅ **Cálculo automático de precios**
- ✅ **Datos bancarios para transferencia**
- ✅ **Redirección a MercadoPago**

### Panel Admin
- ✅ **Interfaz completa de gestión**
- ✅ **Filtros y búsqueda**
- ✅ **Modal de detalles**
- ✅ **Actualización de estados**

## 🚀 **Ventajas del Sistema**

1. **Unificado:** Todos los pedidos en una sola tabla
2. **Completo:** Información detallada de cliente y productos
3. **Flexible:** Soporta múltiples métodos de pago
4. **Escalable:** Paginación y filtros para muchos pedidos
5. **Auditable:** Historial completo de cambios de estado
6. **Seguro:** Autenticación y autorización en todos los endpoints

## 🔍 **Monitoreo y Debug**

- ✅ **Logs detallados** en cada operación
- ✅ **Debug de precios** y cálculos
- ✅ **Validación de datos** en cada endpoint
- ✅ **Manejo de errores** robusto
