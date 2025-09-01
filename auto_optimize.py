#!/usr/bin/env python3
"""
Script de automatización para optimización de imágenes
Monitorea nuevas imágenes y las optimiza automáticamente
"""

import os
import time
import glob
from datetime import datetime
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from image_processor import image_processor

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('image_optimization.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ImageOptimizationHandler(FileSystemEventHandler):
    """Maneja eventos de archivos para optimización automática"""
    
    def __init__(self):
        self.processed_files = set()
    
    def on_created(self, event):
        """Se ejecuta cuando se crea un nuevo archivo"""
        if event.is_directory:
            return
        
        file_path = event.src_path
        if self._is_image_file(file_path) and file_path not in self.processed_files:
            logger.info(f"🆕 Nueva imagen detectada: {file_path}")
            self.processed_files.add(file_path)
            
            # Esperar un poco para asegurar que el archivo esté completamente escrito
            time.sleep(2)
            
            try:
                if image_processor.optimize_single_image(file_path):
                    logger.info(f"✅ Imagen optimizada: {os.path.basename(file_path)}")
                else:
                    logger.error(f"❌ Error optimizando: {os.path.basename(file_path)}")
            except Exception as e:
                logger.error(f"❌ Error procesando {file_path}: {e}")
    
    def on_moved(self, event):
        """Se ejecuta cuando se mueve/renombra un archivo"""
        if event.is_directory:
            return
        
        dest_path = event.dest_path
        if self._is_image_file(dest_path):
            logger.info(f"📁 Imagen movida/renombrada: {dest_path}")
            # Procesar la imagen en su nueva ubicación
            self.on_created(event)
    
    def _is_image_file(self, file_path):
        """Verifica si el archivo es una imagen"""
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'}
        return os.path.splitext(file_path)[1].lower() in image_extensions

def start_monitoring():
    """Inicia el monitoreo automático de imágenes"""
    logger.info("🚀 Iniciando monitoreo automático de imágenes...")
    
    # Directorio a monitorear
    watch_directory = "assets/images/products"
    
    if not os.path.exists(watch_directory):
        logger.error(f"❌ El directorio {watch_directory} no existe")
        return
    
    # Crear el observer y el handler
    event_handler = ImageOptimizationHandler()
    observer = Observer()
    observer.schedule(event_handler, watch_directory, recursive=False)
    
    # Iniciar el observer
    observer.start()
    logger.info(f"👀 Monitoreando directorio: {watch_directory}")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("⏹️  Deteniendo monitoreo...")
        observer.stop()
    
    observer.join()
    logger.info("✅ Monitoreo detenido")

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
            # Iniciar monitoreo automático
            start_monitoring()
        elif command == "all":
            # Ejecutar todo
            process_existing_images()
            show_stats()
            start_monitoring()
        else:
            print("Comandos disponibles:")
            print("  python auto_optimize.py process  - Procesar imágenes existentes")
            print("  python auto_optimize.py stats    - Mostrar estadísticas")
            print("  python auto_optimize.py cleanup  - Limpiar optimizaciones")
            print("  python auto_optimize.py monitor  - Monitoreo automático")
            print("  python auto_optimize.py all      - Ejecutar todo")
    else:
        # Comportamiento por defecto: procesar imágenes existentes
        process_existing_images()
        show_stats()
