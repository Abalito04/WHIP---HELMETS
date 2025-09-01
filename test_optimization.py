#!/usr/bin/env python3
"""
Script de prueba para verificar la optimización de imágenes
"""

import sys
import os

# Agregar el directorio backend al path
sys.path.append('backend')

try:
    from image_processor import image_processor
    print("✅ Módulo image_processor importado correctamente")
    
    # Probar estadísticas
    print("\n📊 Obteniendo estadísticas...")
    stats = image_processor.get_optimization_stats()
    
    print(f"Imágenes originales: {stats.get('original_images', 0)}")
    print(f"Imágenes optimizadas: {stats.get('optimized_images', 0)}")
    print(f"Tamaño original: {stats.get('original_size_mb', 0)} MB")
    print(f"Tamaño optimizado: {stats.get('optimized_size_mb', 0)} MB")
    print(f"Reducción: {stats.get('size_reduction_percent', 0)}%")
    
    # Probar procesamiento de nuevas imágenes
    print("\n🔄 Procesando imágenes nuevas...")
    result = image_processor.process_new_images()
    print(f"Resultado: {result}")
    
except ImportError as e:
    print(f"❌ Error importando módulo: {e}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n✅ Prueba completada")
