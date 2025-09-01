#!/usr/bin/env python3
"""
Módulo de procesamiento automático de imágenes
Se integra con el backend para optimizar imágenes automáticamente
"""

import os
import shutil
from PIL import Image
import glob
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageProcessor:
    def __init__(self):
        self.input_dir = "assets/images/products"
        self.output_dir = "assets/images/products/optimized"
        self.backup_dir = "assets/images/products/backup"
        
        # Crear directorios si no existen
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Tamaños para diferentes dispositivos
        self.sizes = {
            'thumb': (150, 150),    # Miniaturas
            'small': (300, 300),    # Móvil
            'medium': (600, 600),   # Tablet
            'large': (800, 800),    # Desktop
        }
    
    def process_new_images(self):
        """Procesa solo las imágenes nuevas que no han sido optimizadas"""
        try:
            # Obtener lista de imágenes originales
            original_images = set(glob.glob(os.path.join(self.input_dir, "*.png")))
            original_images.update(glob.glob(os.path.join(self.input_dir, "*.jpg")))
            original_images.update(glob.glob(os.path.join(self.input_dir, "*.jpeg")))
            
            # Obtener lista de imágenes ya optimizadas
            optimized_images = set(glob.glob(os.path.join(self.output_dir, "*.webp")))
            
            # Encontrar imágenes nuevas
            new_images = []
            for img_path in original_images:
                base_name = os.path.splitext(os.path.basename(img_path))[0]
                if not any(base_name in opt_img for opt_img in optimized_images):
                    new_images.append(img_path)
            
            if not new_images:
                logger.info("No hay imágenes nuevas para procesar")
                return {"processed": 0, "message": "No hay imágenes nuevas"}
            
            logger.info(f"Procesando {len(new_images)} imágenes nuevas...")
            
            processed_count = 0
            for img_path in new_images:
                if self.optimize_single_image(img_path):
                    processed_count += 1
            
            return {
                "processed": processed_count,
                "message": f"Procesadas {processed_count} imágenes nuevas"
            }
            
        except Exception as e:
            logger.error(f"Error procesando imágenes: {e}")
            return {"processed": 0, "error": str(e)}
    
    def optimize_single_image(self, image_path):
        """Optimiza una sola imagen"""
        try:
            filename = os.path.splitext(os.path.basename(image_path))[0]
            
            # Crear backup de la imagen original
            backup_path = os.path.join(self.backup_dir, os.path.basename(image_path))
            if not os.path.exists(backup_path):
                shutil.copy2(image_path, backup_path)
            
            # Abrir imagen
            with Image.open(image_path) as img:
                # Preservar transparencia para PNG
                if img.mode == 'P':
                    img = img.convert('RGBA')
                elif img.mode == 'LA':
                    img = img.convert('RGBA')
                # Para imágenes RGB sin transparencia, mantener como están
                
                # Generar diferentes tamaños
                for size_name, size in self.sizes.items():
                    img_resized = img.copy()
                    img_resized.thumbnail(size, Image.Resampling.LANCZOS)
                    
                    # Guardar como WebP preservando transparencia
                    output_path = os.path.join(self.output_dir, f"{filename}_{size_name}.webp")
                    if img_resized.mode == 'RGBA':
                        img_resized.save(output_path, 'WEBP', quality=85, optimize=True, lossless=False)
                    else:
                        img_resized.save(output_path, 'WEBP', quality=85, optimize=True)
                
                # Guardar versión original en WebP
                original_webp = os.path.join(self.output_dir, f"{filename}.webp")
                if img.mode == 'RGBA':
                    img.save(original_webp, 'WEBP', quality=90, optimize=True, lossless=False)
                else:
                    img.save(original_webp, 'WEBP', quality=90, optimize=True)
                
                logger.info(f"OK - Optimizada: {filename}")
                return True
                
        except Exception as e:
            logger.error(f"ERROR - Procesando {image_path}: {e}")
            return False
    
    def get_optimized_image_path(self, original_path, size='medium'):
        """Obtiene la ruta de la imagen optimizada"""
        if not original_path:
            return None
        
        base_name = os.path.splitext(os.path.basename(original_path))[0]
        optimized_path = os.path.join(self.output_dir, f"{base_name}_{size}.webp")
        
        # Si no existe la versión optimizada, devolver la original
        if not os.path.exists(optimized_path):
            return original_path
        
        return optimized_path
    
    def cleanup_old_optimizations(self):
        """Limpia optimizaciones de imágenes que ya no existen"""
        try:
            # Obtener nombres base de imágenes originales
            original_bases = set()
            for ext in ['*.png', '*.jpg', '*.jpeg']:
                for img_path in glob.glob(os.path.join(self.input_dir, ext)):
                    base_name = os.path.splitext(os.path.basename(img_path))[0]
                    original_bases.add(base_name)
            
            # Eliminar optimizaciones de imágenes que ya no existen
            removed_count = 0
            for opt_path in glob.glob(os.path.join(self.output_dir, "*.webp")):
                opt_name = os.path.basename(opt_path)
                base_name = opt_name.split('_')[0] if '_' in opt_name else opt_name.replace('.webp', '')
                
                if base_name not in original_bases:
                    os.remove(opt_path)
                    removed_count += 1
                    logger.info(f"Eliminada optimizacion obsoleta: {opt_name}")
            
            return removed_count
            
        except Exception as e:
            logger.error(f"Error limpiando optimizaciones: {e}")
            return 0
    
    def get_optimization_stats(self):
        """Obtiene estadísticas de optimización"""
        try:
            original_count = len(glob.glob(os.path.join(self.input_dir, "*.png")))
            original_count += len(glob.glob(os.path.join(self.input_dir, "*.jpg")))
            original_count += len(glob.glob(os.path.join(self.input_dir, "*.jpeg")))
            
            optimized_count = len(glob.glob(os.path.join(self.output_dir, "*.webp")))
            
            # Calcular tamaño total
            original_size = sum(os.path.getsize(f) for f in glob.glob(os.path.join(self.input_dir, "*.*")) 
                              if f.lower().endswith(('.png', '.jpg', '.jpeg')))
            optimized_size = sum(os.path.getsize(f) for f in glob.glob(os.path.join(self.output_dir, "*.webp")))
            
            return {
                "original_images": original_count,
                "optimized_images": optimized_count,
                "original_size_mb": round(original_size / (1024 * 1024), 2),
                "optimized_size_mb": round(optimized_size / (1024 * 1024), 2),
                "size_reduction_percent": round((1 - optimized_size / original_size) * 100, 1) if original_size > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadisticas: {e}")
            return {}

# Instancia global
image_processor = ImageProcessor()
