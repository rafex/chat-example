#!/usr/bin/env python3
"""
Prueba del Chat Genérico con Herramientas
"""

import sys
import os

# Configurar paths
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.services.generic_chat_service import GenericChatService

print("="*60)
print("PRUEBA: CHAT GENÉRICO CON HERRAMIENTAS")
print("="*60)

# Inicializar servicio
service = GenericChatService()

# Pruebas
test_cases = [
    ("Hola", "Saludo"),
    ("¿Cómo estás?", "Conversación general"),
    ("¿Qué es la inteligencia artificial?", "Consulta general"),
    ("¿Cómo está el clima en Madrid?", "Consulta de clima"),
    ("¿Qué tiempo hace en Barcelona?", "Consulta de clima"),
    ("adiós", "Despedida"),
]

print("\nEjecutando pruebas...\n")

for message, description in test_cases:
    print(f"📝 {description}: '{message}'")
    result = service.chat(message)
    print(f"   Tipo: {result['type']}")
    if result.get('tool_used'):
        print(f"   Herramienta: {result['tool_used']} -> {result['tool_args']}")
    print(f"   Respuesta: {result['response'][:80]}...")
    print()

print("="*60)
print("✅ PRUEBAS COMPLETADAS")
print("="*60)
print("\nEl chat genérico está listo para usar:")
print("  cd poc/agent-weather")
print("  source venv/bin/activate")
print("  python src/chat_cli_generic.py")
