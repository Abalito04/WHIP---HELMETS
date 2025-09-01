#!/usr/bin/env python3
"""
Script simplificado de optimización de imágenes
Sin dependencias externas, solo Pillow
"""

import os
import time
import glob
from datetime import datetime
import logging
from image_processor import image_processor

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_existing_images():
    """Procesa todas las imágenes existentes que no han sido optimizadas"""
    logger.info("🔄 Procesando imágenes existentes...")
    
    try:
        result = image_processor.process_new_images()
        logger.info(f"✅ {result.get('message', 'Procesamiento completado')}")
        return result
    except Exception as e:
        logger.error(f"❌ Error procesando imágenes existentes: {e}")
        return {"error": str(e)}

def show_stats():
    """Muestra estadísticas de optimización"""
    try:
        stats = image_processor.get_optimization_stats()
        logger.info("📊 Estadísticas de optimización:")
        logger.info(f"   Imágenes originales: {stats.get('original_images', 0)}")
        logger.info(f"   Imágenes optimizadas: {stats.get('optimized_images', 0)}")
        logger.info(f"   Tamaño original: {stats.get('original_size_mb', 0)} MB")
        logger.info(f"   Tamaño optimizado: {stats.get('optimized_size_mb', 0)} MB")
        logger.info(f"   Reducción: {stats.get('size_reduction_percent', 0)}%")
    except Exception as e:
        logger.error(f"❌ Error obteniendo estadísticas: {e}")

def cleanup_old_optimizations():
    """Limpia optimizaciones obsoletas"""
    logger.info("🧹 Limpiando optimizaciones obsoletas...")
    
    try:
        removed_count = image_processor.cleanup_old_optimizations()
        logger.info(f"✅ Eliminadas {removed_count} optimizaciones obsoletas")
        return removed_count
    except Exception as e:
        logger.error(f"❌ Error limpiando optimizaciones: {e}")
        return 0

def simple_monitor():
    """Monitoreo simple que verifica cada 30 segundos"""
    logger.info("🚀 Iniciando monitoreo simple de imágenes...")
    logger.info("👀 Verificando nuevas imágenes cada 30 segundos...")
    logger.info("⏹️  Presiona Ctrl+C para detener")
    
    last_check = 0
    
    try:
        while True:
            current_time = time.time()
            
            # Verificar cada 30 segundos
            if current_time - last_check >= 30:
                logger.info("🔍 Verificando nuevas imágenes...")
                result = image_processor.process_new_images()
                
                if result.get('processed', 0) > 0:
                    logger.info(f"✅ {result.get('message', 'Procesamiento completado')}")
                
                last_check = current_time
            
            time.sleep(5)  # Dormir 5 segundos entre verificaciones
            
    except KeyboardInterrupt:
        logger.info("⏹️  Monitoreo detenido por el usuario")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "process":
            # Procesar imágenes existentes
            process_existing_images()
        elif command == "stats":
            # Mostrar estadísticas
            show_stats()
        elif command == "cleanup":
            # Limpiar optimizaciones obsoletas
            cleanup_old_optimizations()
        elif command == "monitor":
            # Iniciar monitoreo simple
            simple_monitor()
        elif command == "all":
            # Ejecutar todo
            process_existing_images()
            show_stats()
            simple_monitor()
        else:
            print("Comandos disponibles:")
            print("  python simple_optimize.py process  - Procesar imágenes existentes")
            print("  python simple_optimize.py stats    - Mostrar estadísticas")
            print("  python simple_optimize.py cleanup  - Limpiar optimizaciones")
            print("  python simple_optimize.py monitor  - Monitoreo simple")
            print("  python simple_optimize.py all      - Ejecutar todo")
    else:
        # Comportamiento por defecto: procesar imágenes existentes
        process_existing_images()
        show_stats()
