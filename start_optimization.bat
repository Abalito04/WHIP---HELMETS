@echo off
echo ========================================
echo   MONITOREO AUTOMATICO DE IMAGENES
echo   WHIP HELMETS - OPTIMIZACION
echo ========================================
echo.

echo Instalando dependencias...
pip install Pillow==10.1.0 watchdog==3.0.0

echo.
echo Iniciando monitoreo automatico...
echo Las nuevas imagenes se optimizaran automaticamente
echo Presiona Ctrl+C para detener
echo.

python auto_optimize.py monitor

pause
