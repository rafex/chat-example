#!/usr/bin/env python3
"""
Chat CLI Interactivo para el Agente Meteorológico
Accede al proyecto de weather agent usando paths relativos
"""

import sys
import os
import uuid

# Configurar paths para acceder al proyecto de weather
# El chatCLI está en poc/chatCLI, el weather está en poc/agent-weather
chat_cli_dir = os.path.dirname(os.path.abspath(__file__))
chatCLI_root = os.path.dirname(chat_cli_dir)  # poc/chatCLI
poc_root = os.path.dirname(chatCLI_root)      # poc
agent_weather_path = os.path.join(poc_root, 'agent-weather', 'src')

print(f"DEBUG: chat_cli_dir = {chat_cli_dir}")
print(f"DEBUG: chatCLI_root = {chatCLI_root}")
print(f"DEBUG: poc_root = {poc_root}")
print(f"DEBUG: agent_weather_path = {agent_weather_path}")

# Añadir los paths al sys.path
sys.path.insert(0, agent_weather_path)
sys.path.insert(0, os.path.join(chatCLI_root, 'src'))

# Ahora importamos los módulos
from schemas.chat import ChatSession, MessageType, Message
from services.weather_chat_agent import WeatherChatAgent


def clear_screen():
    """Limpiar la pantalla"""
    os.system('clear' if os.name == 'posix' else 'cls')


def print_banner():
    """Mostrar banner del chat"""
    banner = """
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║              🌤️  CHAT CLIMATOLÓGICO CON DEEPSEEK  🤖                 ║
║                                                                      ║
║  Bienvenido al asistente meteorológico interactivo                   ║
║  Pregunta sobre el clima de cualquier ciudad del mundo               ║
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
        return f"\n🤖 CLIMA-BOT [{timestamp}]:\n{msg.content}"
    elif msg.type == MessageType.SYSTEM:
        return f"\nℹ️  SISTEMA: {msg.content}"
    else:
        return f"\n{msg.content}"


def main():
    """Función principal del chat"""
    try:
        clear_screen()
        print_banner()

        # Inicializar sesión y agente
        session_id = str(uuid.uuid4())[:8]
        chat_session = ChatSession(id=session_id)
        agent = WeatherChatAgent()

        print(f"\n💡 Sesión iniciada: {session_id}")
        print("💡 Escribe 'salir' o 'exit' para terminar")
        print("💡 Escribe 'ayuda' para ver comandos disponibles")
        print("-" * 70)

        # Mensaje de bienvenida del asistente
        welcome_msg = Message(
            type=MessageType.ASSISTANT,
            content="👋 ¡Hola! Soy tu asistente meteorológico.\n"
                    "Pregúntame sobre el clima de cualquier ciudad, por ejemplo:\n"
                    "• '¿Cómo está el clima en Madrid?'\n"
                    "• '¿Qué tiempo hace en Barcelona?'\n"
                    "• 'Temperatura en Londres'\n\n"
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

                if user_input == '':
                    continue

                # Procesar mensaje con el agente
                response = agent.process_message(user_input)

                # Guardar en el historial
                chat_session.add_message(MessageType.USER, user_input)
                chat_session.add_message(response.type, response.content, response.data)

                # Mostrar respuesta
                print(format_message(response))

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
        print("3. Las API keys estén configuradas en ../agent-weather/.env")
        sys.exit(1)


if __name__ == "__main__":
    main()
