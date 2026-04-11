#!/usr/bin/env python3
"""
Script de prueba para verificar la integración de DeepSeek con el agente meteorológico.
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agents.weather_agent import run_weather_agent
from src.services.deepseek_service import DeepSeekService
from src.config import Config

def test_deepseek_service():
    """Prueba el servicio de DeepSeek directamente"""
    print("=== Probando DeepSeek Service ===")
    try:
        service = DeepSeekService()
        weather_data = {
            "location": "Madrid",
            "temperature_celsius": 25.5,
            "condition": "Cielo despejado",
            "humidity": 45,
            "wind_speed": 3.2
        }
        recommendations = service.generate_recommendations(weather_data)
        print(f"Recomendaciones generadas: {recommendations}")
        return True
    except Exception as e:
        print(f"Error con DeepSeek: {e}")
        return False

def test_weather_agent():
    """Prueba el agente meteorológico completo"""
    print("\n=== Probando Agente Meteorológico ===")
    try:
        result = run_weather_agent("Madrid")
        print(f"Resultado: {result}")
        return result.get("success", False)
    except Exception as e:
        print(f"Error con el agente: {e}")
        return False

def show_config():
    """Muestra la configuración actual"""
    print("\n=== Configuración Actual ===")
    print(f"OPENWEATHER_API_KEY: {'Configurada' if Config.OPENWEATHER_API_KEY else 'Faltante'}")
    print(f"LLM_PROVIDER_API_KEY: {'Configurada' if Config.get_llm_api_key() else 'Faltante'}")
    print(f"LLM_PROVIDER_API_BASE: {Config.get_llm_api_base()}")
    print(f"LLM_PROVIDER_MODEL: {Config.get_llm_model()}")

if __name__ == "__main__":
    show_config()

    # Prueba básica del servicio DeepSeek
    deepseek_ok = test_deepseek_service()

    # Prueba del agente completo
    agent_ok = test_weather_agent()

    print(f"\n=== Resumen ===")
    print(f"DeepSeek Service: {'✅ OK' if deepseek_ok else '❌ FALLÓ'}")
    print(f"Agente Meteorológico: {'✅ OK' if agent_ok else '❌ FALLÓ'}")

    if deepseek_ok and agent_ok:
        print("\n🎉 ¡Todas las pruebas pasaron!")
        sys.exit(0)
    else:
        print("\n⚠️ Algunas pruebas fallaron (puede deberse a API keys inválidas)")
        sys.exit(1)
