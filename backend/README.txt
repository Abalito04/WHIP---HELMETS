
# Backend WHIP-HELMETS (Flask + SQLite)

## Requisitos
- Python 3.10+
- Instalar dependencias:
```
pip install -r requirements.txt
```

## Ejecutar
```
python server.py
```
La API arranca en: http://127.0.0.1:5000

## Endpoints principales
- `GET /api/health` → estado de la API
- `GET /api/products` → lista de productos
- `POST /api/products` → crear
- `PUT /api/products/<id>` → actualizar
- `DELETE /api/products/<id>` → eliminar
- `POST /api/seed` → insertar productos de ejemplo
