#!/usr/bin/env python3
"""Script para verificar configuración de OpenRouter"""

import sys
import os

# Configurar paths
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
orquestador_src = os.path.join(project_root, 'poc', 'agent-orquestador', 'src')
agent_weather_src = os.path.join(project_root, 'poc', 'agent-weather', 'src')

sys.path.insert(0, orquestador_src)
sys.path.insert(0, os.path.join(orquestador_src, 'agents'))
sys.path.insert(0, os.path.join(orquestador_src, 'schemas'))
sys.path.insert(0, os.path.join(orquestador_src, 'services'))
sys.path.insert(0, agent_weather_src)
sys.path.insert(0, os.path.join(agent_weather_src, 'services'))
sys.path.insert(0, os.path.join(agent_weather_src, 'schemas'))

from deepseek_service import LLMProviderService

print("=" * 80)
print("VERIFICACIÓN DE CONFIGURACIÓN DE OPENROUTER")
print("=" * 80)

# Crear instancia del servicio LLM
try:
    llm_service = LLMProviderService()
    print(f"✅ LLM Provider inicializado correctamente")
    print(f"   API Base: {llm_service.client.base_url}")
    print(f"   Modelo: {llm_service.model}")
    print(f"   Disponible: {llm_service.available}")

    # Probar una solicitud simple
    print("\nProbando solicitud al LLM...")
    messages = [
        {"role": "system", "content": "Eres un asistente útil."},
        {"role": "user", "content": "¿Cuál es el capital de Francia?"}
    ]

    response = llm_service.chat(messages)
    print(f"\n✅ Respuesta del LLM:")
    print(f"   {response}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
