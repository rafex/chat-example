#!/usr/bin/env python3
"""
Demo del Chat Genérico con Herramientas
"""

import sys
import os

# Configurar paths
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.services.generic_chat_service import GenericChatService

print("="*60)
print("演示: CHAT GENÉRICO CON HERRAMIENTAS")
print("="*60)
print("\nCaracterísticas:")
print("• Conversación general con el LLM")
print("• Herramienta get_weather para consultas climáticas")
print("• Preparado para integrar MCP en el futuro")
print()

# Inicializar servicio
service = GenericChatService()

# Pruebas
test_cases = [
    ("Hola, ¿cómo estás?", "Saludo y conversación"),
    ("¿Qué es la inteligencia artificial?", "Consulta general"),
    ("¿Cómo está el clima en Madrid?", "Consulta de clima"),
    ("¿Qué tiempo hace en Barcelona?", "Consulta de clima (con verbo)"),
    ("Háblame del clima en Nueva York", "Consulta de clima (sin preposición)"),
    ("adiós", "Despedida"),
]

print("Ejecutando pruebas...\n")

for message, description in test_cases:
    print(f"📝 {description}")
    print(f"   Mensaje: '{message}'")
    result = service.chat(message)
    print(f"   Tipo: {result['type']}")
    if result.get('tool_used'):
        print(f"   🔧 Herramienta: {result['tool_used']} -> {result['tool_args']}")
    print(f"   Respuesta: {result['response'][:100]}...")
    print()

print("="*60)
print("✅ DEMO COMPLETADA")
print("="*60)
print("\nPara usar el chat interactivo:")
print("  cd poc/agent-weather")
print("  source venv/bin/activate")
print("  python src/chat_cli_generic.py")
print("\nO usando Just:")
print("  just chat-generic")
