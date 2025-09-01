#!/usr/bin/env python3
"""
Script para optimizar imágenes de productos
Convierte PNG a WebP y genera múltiples tamaños
"""

import os
import sys
from PIL import Image
import glob

def optimize_images():
    """Optimiza todas las imágenes de productos"""
    
    # Rutas de imágenes
    input_dir = "assets/images/products"
    output_dir = "assets/images/products/optimized"
    
    # Crear directorio de salida si no existe
    os.makedirs(output_dir, exist_ok=True)
    
    # Tamaños para diferentes dispositivos
    sizes = {
        'thumb': (150, 150),    # Miniaturas
        'small': (300, 300),    # Móvil
        'medium': (600, 600),   # Tablet
        'large': (800, 800),    # Desktop
        'original': None        # Tamaño original
    }
    
    # Buscar todas las imágenes PNG
    png_files = glob.glob(os.path.join(input_dir, "*.png"))
    
    if not png_files:
        print("No se encontraron imágenes PNG para optimizar")
        return
    
    print(f"Encontradas {len(png_files)} imágenes para optimizar...")
    
    for png_file in png_files:
        try:
            # Abrir imagen
            with Image.open(png_file) as img:
                # Convertir a RGB si es necesario
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Crear fondo blanco para transparencias
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                
                filename = os.path.splitext(os.path.basename(png_file))[0]
                
                # Generar diferentes tamaños
                for size_name, size in sizes.items():
                    if size:
                        # Redimensionar manteniendo proporción
                        img_resized = img.copy()
                        img_resized.thumbnail(size, Image.Resampling.LANCZOS)
                    else:
                        img_resized = img.copy()
                    
                    # Guardar como WebP
                    output_path = os.path.join(output_dir, f"{filename}_{size_name}.webp")
                    img_resized.save(output_path, 'WEBP', quality=85, optimize=True)
                    
                    # También guardar versión original en WebP
                    if size_name == 'original':
                        original_webp = os.path.join(output_dir, f"{filename}.webp")
                        img.save(original_webp, 'WEBP', quality=90, optimize=True)
                
                print(f"✓ Optimizada: {filename}")
                
        except Exception as e:
            print(f"✗ Error procesando {png_file}: {e}")
    
    print("\n¡Optimización completada!")
    print(f"Imágenes optimizadas guardadas en: {output_dir}")

if __name__ == "__main__":
    optimize_images()
