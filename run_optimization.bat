@echo off
echo ========================================
echo   OPTIMIZACION DE IMAGENES - WHIP HELMETS
echo ========================================
echo.

echo Instalando dependencias...
pip install Pillow==10.1.0

echo.
echo Ejecutando optimizacion de imagenes...
python optimize_images.py

echo.
echo ========================================
echo   OPTIMIZACION COMPLETADA
echo ========================================
echo.
echo Las imagenes optimizadas se encuentran en:
echo assets/images/products/optimized/
echo.
pause
