#!/usr/bin/env python3
"""
Script de prueba del chat CLI sin entrada interactiva
"""

import sys
import os

# Configurar paths
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.schemas.chat import ChatSession, MessageType, Message
from src.services.weather_chat_agent import WeatherChatAgent

print("=== PRUEBA DEL CHAT CLI ===\n")

# Test 1: Crear sesión
print("1. Probando creación de sesión...")
session = ChatSession(id="test-session")
session.add_message(MessageType.USER, "Hola")
print("   ✅ Sesión creada")

# Test 2: Instanciar agente
print("\n2. Probando agente...")
agent = WeatherChatAgent()
print("   ✅ Agente instanciado")

# Test 3: Procesar mensaje simple
print("\n3. Probando procesamiento de mensaje...")
response = agent.process_message("Hola")
print(f"   ✅ Respuesta: {response.type}")
print(f"   Contenido: {response.content[:50]}...")

# Test 4: Probar diferentes mensajes
print("\n4. Probando diferentes consultas...")
test_messages = [
    "Hola",
    "¿Cómo está el clima en Madrid?",
    "ayuda",
    "adiós"
]

for msg in test_messages:
    try:
        response = agent.process_message(msg)
        print(f"   - '{msg}': ✅ {response.type}")
    except Exception as e:
        print(f"   - '{msg}': ❌ {e}")

print("\n" + "="*50)
print("✅ PRUEBAS COMPLETADAS")
print("="*50)
print("\nEl chat CLI está listo para usar.")
print("Ejecuta: just chat")
print("O usa: cd poc/agent-weather && source venv/bin/activate && python src/chat_cli.py")
