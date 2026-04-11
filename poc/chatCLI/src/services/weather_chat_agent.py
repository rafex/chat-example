import sys
import os

# Añadir el path del proyecto weather para importar sus componentes
# chatCLI/src/services -> chatCLI/src -> chatCLI -> poc -> agent-weather -> src
chat_cli_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
chatCLI_root = os.path.dirname(chat_cli_dir)  # poc/chatCLI
poc_root = os.path.dirname(chatCLI_root)      # poc
weather_project_path = os.path.join(poc_root, 'agent-weather')

# Añadir el path del proyecto weather completo
sys.path.insert(0, weather_project_path)
sys.path.insert(0, os.path.join(weather_project_path, 'src'))

# Importar desde la estructura completa del proyecto
from agents.weather_agent import run_weather_agent
from services.deepseek_service import DeepSeekService
from schemas.chat import Message, MessageType

class WeatherChatAgent:
    """Agente de chat especializado en clima"""

    def __init__(self):
        self.deepseek_service = None
        try:
            self.deepseek_service = DeepSeekService()
        except Exception as e:
            print(f"⚠️  DeepSeek no disponible: {e}")

    def process_message(self, user_message: str, location: str = "") -> Message:
        """
        Procesa un mensaje del usuario y devuelve una respuesta del agente
        """
        user_message_lower = user_message.lower().strip()

        # Detectar intención de consultar clima
        weather_keywords = ['clima', 'tiempo', 'lluvia', 'sol', 'calor', 'frío', 'frío', 'temperatura', 'weather', 'temperature']

        if any(keyword in user_message_lower for keyword in weather_keywords):
            # Extraer ubicación si se menciona
            ciudad = location
            if not ciudad:
                # Intentar extraer ciudad del mensaje
                words = user_message.split()
                for i, word in enumerate(words):
                    if word.lower() in ['en', 'de', 'para', 'en', 'de']:
                        if i + 1 < len(words):
                            ciudad = words[i + 1]
                            break

            if not ciudad:
                ciudad = "Madrid"  # Ciudad por defecto

            # Ejecutar agente meteorológico
            try:
                result = run_weather_agent(ciudad)

                if result.get('weather_data'):
                    data = result['weather_data']
                    temp_celsius = data['main']['temp'] - 273.15
                    condition = data['weather'][0]['description']

                    response_content = f"🌡️ **Clima en {ciudad}**\n"
                    response_content += f"• Temperatura: {temp_celsius:.1f}°C\n"
                    response_content += f"• Condición: {condition}\n"
                    response_content += f"• Humedad: {data['main']['humidity']}%\n"
                    response_content += f"• Viento: {data['wind']['speed']} m/s\n\n"

                    # Añadir recomendaciones del LLM si están disponibles
                    if result.get('analysis') and result['analysis'].get('recommendations'):
                        response_content += "💡 **Recomendaciones:**\n"
                        for rec in result['analysis']['recommendations']:
                            response_content += f"• {rec}\n"
                else:
                    response_content = f"⚠️ No se pudo obtener el clima de {ciudad}. "
                    response_content += "La API de OpenWeatherMap necesita 2h para activarse si acabas de obtenerla.\n"
                    response_content += "Mientras tanto, puedo darte recomendaciones basadas en tu ubicación actual."

                return Message(type=MessageType.ASSISTANT, content=response_content)

            except Exception as e:
                return Message(
                    type=MessageType.ASSISTANT,
                    content=f"❌ Error al consultar el clima: {str(e)}"
                )

        # Si no es una solicitud de clima, responder genéricamente
        elif any(greeting in user_message_lower for greeting in ['hola', 'hi', 'hey', 'buenos días', 'buenas']):
            return Message(
                type=MessageType.ASSISTANT,
                content="👋 ¡Hola! Soy tu asistente meteorológico. Pregúntame sobre el clima de cualquier ciudad, por ejemplo: '¿Cómo está el clima en Madrid?'"
            )

        elif any(bye in user_message_lower for bye in ['adiós', 'bye', 'hasta luego', 'chao']):
            return Message(
                type=MessageType.ASSISTANT,
                content="👋 ¡Hasta luego! Si necesitas saber el clima, no dudes en preguntar."
            )

        elif 'ayuda' in user_message_lower or 'help' in user_message_lower:
            return Message(
                type=MessageType.ASSISTANT,
                content="""🆘 **AYUDA**

Puedes preguntarme sobre:

• **Clima de ciudades**: "¿Cómo está el clima en Madrid?", "¿Qué tiempo hace en Barcelona?"
• **Temperatura**: "¿Qué temperatura hay en Londres?"
• **Condiciones**: "¿Llueve en París?", "¿Hace calor en Sevilla?"

Simplemente escribe tu consulta y te daré información detallada del clima."""
            )

        else:
            return Message(
                type=MessageType.ASSISTANT,
                content=f"""🤔 No entendí completamente tu mensaje.

Para consultar el clima, prueba con algo como:
• "¿Cómo está el clima en Madrid?"
• "¿Qué tiempo hace en Barcelona?"
• "Temperatura en Londres"

Escribe 'ayuda' para ver más opciones."""
            )
