#!/usr/bin/env python3
"""
Script para limpiar sesiones temporales del orquestador
"""
import shutil
from pathlib import Path

def clean_temp_sessions():
    """Limpia el directorio temporal de sesiones"""
    temp_dir = Path.home() / '.agentes-langgraph' / 'temp_sessions'
    
    if temp_dir.exists():
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
            print('✅ Directorio temporal de sesiones limpiado')
        except Exception as e:
            print(f'⚠️  Error limpiando directorio temporal: {e}')
    else:
        print('ℹ️  No se encontró directorio temporal de sesiones')

if __name__ == '__main__':
    clean_temp_sessions()