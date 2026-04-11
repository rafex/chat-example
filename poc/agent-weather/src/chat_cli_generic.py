#!/usr/bin/env python3
"""
Chat CLI Interactivo Genérico con Herramientas

Este chat permite:
1. Conversación general con el LLM
2. Consultas de clima usando la herramienta get_weather
3. Preparación para integrar MCP en el futuro
"""

import sys
import os
import uuid

# Configurar paths
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.schemas.chat import ChatSession, MessageType, Message
from src.services.generic_chat_service import GenericChatService


def clear_screen():
    """Limpiar la pantalla"""
    os.system('clear' if os.name == 'posix' else 'cls')


def print_banner():
    """Mostrar banner del chat"""
    banner = """
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║              🤖  CHAT CONVERSACIONAL CON HERRAMIENTAS  🧠            ║
║                                                                      ║
║  Asistente conversacional con capacidad de consultar el clima       ║
║  y responder a cualquier consulta general                           ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def format_message(msg):
    """Formatear mensaje para mostrar en consola"""
    timestamp = msg.timestamp.strftime("%H:%M:%S")

    if msg.type == MessageType.USER:
        return f"\n👤 TÚ [{timestamp}]: {msg.content}"
    elif msg.type == MessageType.ASSISTANT:
        return f"\n🤖 ASISTENTE [{timestamp}]:\n{msg.content}"
    elif msg.type == MessageType.SYSTEM:
        return f"\nℹ️  SISTEMA: {msg.content}"
    else:
        return f"\n{msg.content}"


def main():
    """Función principal del chat"""
    try:
        clear_screen()
        print_banner()

        # Inicializar sesión y servicio de chat
        session_id = str(uuid.uuid4())[:8]
        chat_session = ChatSession(id=session_id)
        chat_service = GenericChatService()

        print(f"\n💡 Sesión iniciada: {session_id}")
        print("💡 Escribe 'salir' o 'exit' para terminar")
        print("💡 Escribe 'ayuda' para ver comandos disponibles")
        print("💡 Escribe 'herramientas' para ver herramientas disponibles")
        print("-" * 70)

        # Mensaje de bienvenida del asistente
        welcome_msg = Message(
            type=MessageType.ASSISTANT,
            content="🤖 ¡Hola! Soy tu asistente conversacional.\n"
                    "Puedo conversar sobre cualquier tema y también consultar el clima.\n"
                    "Prueba con:\n"
                    "• '¿Cómo estás?'\n"
                    "• '¿Cómo está el clima en Madrid?'\n"
                    "• 'Explícame el concepto de inteligencia artificial'\n\n"
                    "Escribe 'ayuda' para más información."
        )
        chat_session.add_message(welcome_msg.type, welcome_msg.content)
        print(format_message(welcome_msg))

        # Bucle principal del chat
        while True:
            try:
                # Leer entrada del usuario
                user_input = input("\n👤 Tu mensaje: ").strip()

                # Comandos especiales
                if user_input.lower() in ['salir', 'exit', 'quit', 'adiós']:
                    goodbye_msg = Message(
                        type=MessageType.ASSISTANT,
                        content="👋 ¡Hasta pronto! Que tengas un buen día."
                    )
                    chat_session.add_message(goodbye_msg.type, goodbye_msg.content)
                    print(format_message(goodbye_msg))
                    break

                if user_input.lower() in ['limpiar', 'clear', 'cls']:
                    clear_screen()
                    print_banner()
                    print("\n💡 Pantalla limpiada.")
                    continue

                if user_input.lower() in ['historial', 'history']:
                    print("\n📜 Historial de la sesión:")
                    for msg in chat_session.messages[-5:]:
                        print(format_message(msg))
                    continue

                if user_input.lower() in ['herramientas', 'tools']:
                    print("\n🔧 HERRAMIENTAS DISPONIBLES:")
                    print("• get_weather(location): Consulta el clima de una ciudad")
                    continue

                if user_input == '':
                    continue

                # Preparar historial para el servicio de chat
                conversation_history = [
                    {"role": msg.type.value, "content": msg.content}
                    for msg in chat_session.messages
                ]

                # Procesar mensaje con el servicio de chat
                result = chat_service.chat(user_input, conversation_history)

                # Mostrar indicador si se usó una herramienta
                if result.get('tool_used'):
                    print(f"\n🔧 Usando herramienta: {result['tool_used']} con {result['tool_args']}")

                # Crear mensaje del asistente
                assistant_msg = Message(
                    type=MessageType.ASSISTANT,
                    content=result['response']
                )

                # Guardar en el historial
                chat_session.add_message(MessageType.USER, user_input)
                chat_session.add_message(assistant_msg.type, assistant_msg.content, result)

                # Mostrar respuesta
                print(format_message(assistant_msg))

            except KeyboardInterrupt:
                print("\n\n👋 Saliendo del chat...")
                break
            except Exception as e:
                error_msg = Message(
                    type=MessageType.SYSTEM,
                    content=f"❌ Error: {str(e)}"
                )
                chat_session.add_message(error_msg.type, error_msg.content)
                print(format_message(error_msg))

    except Exception as e:
        print(f"\n❌ Error al iniciar el chat: {e}")
        print("\nVerifica que:")
        print("1. El entorno virtual esté activado")
        print("2. Las dependencias estén instaladas")
        print("3. Las API keys estén configuradas en .env")
        sys.exit(1)


if __name__ == "__main__":
    main()
