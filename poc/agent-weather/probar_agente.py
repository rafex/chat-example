#!/usr/bin/env python3
"""
Script de prueba interactivo para el agente meteorológico con DeepSeek.
Ejecuta este script para probar el agente con cualquier ciudad.
"""

import sys
import os
import json
from datetime import datetime

# Asegurar que estamos en el directorio correcto
project_root = os.path.dirname(os.path.abspath(__file__))
os.chdir(project_root)

# Importar el agente
sys.path.insert(0, project_root)
from src.agents.weather_agent import run_weather_agent

def imprimir_banner():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║       🌤️  AGENTE METEOROLÓGICO CON DEEPSEEK  🧠           ║
    ║                                                            ║
    ║  • LangGraph: Orquestación de flujo                       ║
    ║  • OpenWeatherMap: Datos climáticos reales                 ║
    ║  • DeepSeek LLM: Recomendaciones inteligentes              ║
    ╚════════════════════════════════════════════════════════════╝
    """)

def consultar_clima():
    """Consulta el clima de una ciudad"""
    print("\n📍 CONSULTA DE CLIMA")
    print("-" * 50)
    
    ciudad = input("Ingresa la ciudad (ej: Madrid, Barcelona, Londres): ").strip()
    
    if not ciudad:
        print("❌ Debes ingresar una ciudad válida")
        return
    
    print(f"\n⏳ Consultando clima para: {ciudad}...")
    print("-" * 50)
    
    try:
        resultado = run_weather_agent(ciudad)
        
        if resultado['success']:
            print("✅ ¡Consulta exitosa!\n")
            
            # Mostrar datos climáticos
            if resultado['weather_data']:
                data = resultado['weather_data']
                print("🌡️  DATOS CLIMÁTICOS:")
                print(f"   • Ciudad: {data['name']}, {data['sys']['country']}")
                print(f"   • Temperatura: {data['main']['temp'] - 273.15:.1f}°C")
                print(f"   • Sensación térmica: {data['main']['feels_like'] - 273.15:.1f}°C")
                print(f"   • Condición: {data['weather'][0]['description']}")
                print(f"   • Humedad: {data['main']['humidity']}%")
                print(f"   • Viento: {data['wind']['speed']} m/s")
                print(f"   • Presión: {data['main']['pressure']} hPa")
            else:
                print("⚠️  No se pudieron obtener datos climáticos")
                print("   (Espera 2h si acabas de obtener la API key de OpenWeatherMap)")
            
            # Mostrar análisis y recomendaciones
            if resultado['analysis']:
                analysis = resultado['analysis']
                print("\n📊 ANÁLISIS:")
                print(f"   • Localidad: {analysis['location']}")
                print(f"   • Temperatura: {analysis['temperature_celsius']:.1f}°C")
                print(f"   • Condición: {analysis['condition']}")
                
                print("\n💡 RECOMENDACIONES:")
                for i, rec in enumerate(analysis['recommendations'], 1):
                    print(f"   {i}. {rec}")
            else:
                print("\n💡 RECOMENDACIONES:")
                for rec in resultado['recommendations']:
                    print(f"   • {rec}")
                    
        else:
            print("❌ Error en la consulta")
            if 'error' in resultado:
                print(f"   Error: {resultado['error']}")
    
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        print("   Verifica que las API keys estén configuradas en .env")

def mostrar_info():
    """Muestra información del sistema"""
    print("\nℹ️  INFORMACIÓN DEL SISTEMA")
    print("-" * 50)
    
    try:
        from src.config import Config
        
        print("Configuración actual:")
        print(f"  • OpenWeatherMap API: {'✅ Configurada' if Config.OPENWEATHER_API_KEY else '❌ Faltante'}")
        print(f"  • DeepSeek API: {'✅ Configurada' if Config.DEEPSEEK_API_KEY else '❌ Faltante'}")
        print(f"  • Modelo DeepSeek: {Config.DEEPSEEK_MODEL}")
        print(f"  • URL API DeepSeek: {Config.DEEPSEEK_API_BASE}")
        
        # Verificar .env
        env_path = os.path.join(project_root, '.env')
        if os.path.exists(env_path):
            print(f"\n📁 Archivo .env: {env_path}")
            print("   (contiene tus API keys - no compartir)")
        else:
            print("\n⚠️  Archivo .env no encontrado")
            print("   Ejecuta: cp .env.example .env")
            
    except Exception as e:
        print(f"Error al leer configuración: {e}")

def main():
    """Menú principal"""
    imprimir_banner()
    
    while True:
        print("\n📋 MENÚ PRINCIPAL")
        print("-" * 50)
        print("1. 🌤️  Consultar clima de una ciudad")
        print("2. ℹ️  Mostrar información del sistema")
        print("3. 🚀 Ejecutar ejemplo rápido (Madrid)")
        print("4. ❌ Salir")
        print("-" * 50)
        
        opcion = input("\nSelecciona una opción (1-4): ").strip()
        
        if opcion == '1':
            consultar_clima()
        elif opcion == '2':
            mostrar_info()
        elif opcion == '3':
            print("\n⚡ Ejecutando ejemplo rápido con Madrid...")
            try:
                resultado = run_weather_agent('Madrid')
                print(json.dumps(resultado, indent=2, ensure_ascii=False))
            except Exception as e:
                print(f"Error: {e}")
        elif opcion == '4':
            print("\n👋 ¡Hasta pronto!")
            break
        else:
            print("❌ Opción no válida")
        
        input("\nPresiona Enter para continuar...")

if __name__ == "__main__":
    main()
