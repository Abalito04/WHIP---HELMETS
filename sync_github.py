#!/usr/bin/env python3
"""
Script para sincronizar el repositorio de GitHub con el proyecto local optimizado
"""

import os
import subprocess
import sys

def run_command(command, description):
    """Ejecutar comando y mostrar resultado"""
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[OK] {description} completado")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"[ERROR] {description} falló:")
            print(result.stderr)
            return False
        return True
    except Exception as e:
        print(f"[ERROR] {description} falló: {e}")
        return False

def check_git_status():
    """Verificar estado de Git"""
    print("VERIFICANDO ESTADO DE GIT")
    print("=" * 40)
    
    # Verificar si estamos en un repositorio Git
    if not os.path.exists('.git'):
        print("[ERROR] No se encontró repositorio Git")
        print("Ejecuta: git init")
        return False
    
    # Verificar estado
    run_command("git status", "Verificando estado del repositorio")
    return True

def sync_with_github():
    """Sincronizar con GitHub"""
    print("\nSINCRONIZANDO CON GITHUB")
    print("=" * 40)
    
    # Agregar todos los cambios
    if not run_command("git add .", "Agregando archivos al staging"):
        return False
    
    # Verificar qué se va a commitear
    run_command("git status", "Verificando archivos a commitear")
    
    # Hacer commit
    commit_message = "🧹 Optimización del proyecto: eliminados 38 archivos innecesarios"
    if not run_command(f'git commit -m "{commit_message}"', "Haciendo commit de optimización"):
        return False
    
    # Push a GitHub
    if not run_command("git push origin master", "Subiendo cambios a GitHub"):
        return False
    
    print("\n✅ SINCRONIZACIÓN COMPLETADA")
    print("El repositorio de GitHub ahora está actualizado con la versión optimizada")
    return True

def main():
    print("SINCRONIZACIÓN CON GITHUB")
    print("=" * 50)
    print("Este script sincronizará tu proyecto local optimizado con GitHub")
    print("Eliminando archivos innecesarios del repositorio remoto")
    
    # Verificar estado de Git
    if not check_git_status():
        return
    
    # Continuar automáticamente
    print("\nContinuando con la sincronización automática...")
    
    # Sincronizar
    if sync_with_github():
        print("\n🎉 ¡SINCRONIZACIÓN EXITOSA!")
        print("Tu repositorio de GitHub ahora está optimizado")
        print("Visita: https://github.com/Abalito04/WHIP---HELMETS")
    else:
        print("\n❌ Error en la sincronización")
        print("Revisa los mensajes de error arriba")

if __name__ == "__main__":
    main()
