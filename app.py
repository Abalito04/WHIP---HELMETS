#!/usr/bin/env python3
"""
Archivo principal para Railway
Importa y ejecuta el servidor Flask desde el backend
"""

import os
import sys

# Agregar el directorio backend al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Cambiar al directorio backend
os.chdir('backend')

# Importar y ejecutar el servidor
if __name__ == "__main__":
    from server import app, init_db
    
    # Inicializar bases de datos
    init_db()
    
    # Configuración para Railway
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    app.run(host="0.0.0.0", port=port, debug=debug)
