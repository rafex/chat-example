#!/usr/bin/env python3
"""
Demo del Chat CLI - Muestra funcionalidad sin interacción
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.schemas.chat import ChatSession, MessageType, Message
from src.services.weather_chat_agent import WeatherChatAgent

print("="*60)
print("演示: CHAT CLI - AGENTE METEOROLÓGICO")
print("="*60)

# Inicializar
session = ChatSession(id="demo-001")
agent = WeatherChatAgent()

print("\n1. Mensaje de bienvenida:")
response = agent.process_message("Hola")
print(f"   {response.content}")

print("\n2. Consulta de ayuda:")
response = agent.process_message("ayuda")
print(f"   {response.content[:100]}...")

print("\n3. Consulta de clima:")
response = agent.process_message("¿Cómo está el clima en Madrid?")
print(f"   Respuesta generada: {response.type}")
print(f"   Contenido: {response.content[:150]}...")

print("\n4. Mensaje de despedida:")
response = agent.process_message("adiós")
print(f"   {response.content}")

print("\n" + "="*60)
print("✅ Demo completada exitosamente")
print("="*60)
print("\nPara usar el chat interactivo:")
print("  cd poc/agent-weather")
print("  source venv/bin/activate")
print("  python src/chat_cli.py")
print("\nO usando Just:")
print("  just chat")
