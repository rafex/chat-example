"""
Servicio de chat genérico con herramientas.

Este módulo implementa un asistente conversacional que:
1. Usa el LLM para respuestas generales
2. Tiene herramientas disponibles (como consultar el clima)
3. Está preparado para integrar MCP en el futuro
"""

from typing import Dict, List, Optional, Any
from enum import Enum
import json

from src.config import Config
from src.agents.weather_agent import run_weather_agent
from src.services.deepseek_service import DeepSeekService
from src.services.mcp_service import HelloMCPServer


class ToolType(str, Enum):
    WEATHER = "weather"
    UNKNOWN = "unknown"


class GenericChatService:
    """Servicio de chat genérico con herramientas"""

    def __init__(self):
        self.llm_service = None
        self.mcp_servers = {}
        
        # Definir herramientas del sistema
        self.tools = {
            "get_weather": {
                "name": "get_weather",
                "description": "Obtiene información del clima de una ubicación específica",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "Nombre de la ciudad o ubicación"
                        }
                    },
                    "required": ["location"]
                }
            },
            "say_hello": {
                "name": "say_hello",
                "description": "Envía un saludo en diferentes idiomas",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Nombre de la persona a saludar (opcional)"
                        },
                        "lang": {
                            "type": "string",
                            "description": "Idioma del saludo (en, es, fr, etc.)"
                        }
                    },
                    "required": []
                }
            }
        }
        
        # Inicializar LLM service
        try:
            self.llm_service = DeepSeekService()
        except Exception as e:
            print(f"⚠️  No se pudo inicializar LLM: {e}")
            self.llm_service = None
        
        # Inicializar servidores MCP
        self._init_mcp_servers()
    
    def _init_mcp_servers(self):
        """Inicializa los servidores MCP"""
        try:
            from src.services.mcp_service import HelloMCPServer
            
            # Inicializar el servidor MCP de saludos
            hello_server = HelloMCPServer()
            if hello_server.start():
                self.mcp_servers["hello"] = hello_server
                print(f"✅ Servidor MCP 'hello' iniciado")
            else:
                print(f"⚠️ No se pudo iniciar el servidor MCP 'hello'")
        except Exception as e:
            print(f"⚠️  Error inicializando servidores MCP: {e}")

    def get_system_prompt(self) -> str:
        """Prompt del sistema para el asistente"""
        return f"""Eres un asistente conversacional útil y amigable.

MODELO:
- Usas el modelo {self.llm_service.model if self.llm_service else 'LLM'}
- Estás ejecutando en {self.llm_service.client.base_url if self.llm_service else 'URL desconocida'}
- Interfaz: OpenAI-compatible

CAPACIDADES:
- Puedes conversar sobre cualquier tema general
- Cuando alguien te pregunte sobre el clima, usa la herramienta get_weather
- Responde siempre en español de forma natural y conversacional

INSTRUCCIONES:
- Sé conciso pero informativo
- Usa emojis cuando sea apropiado
- Si te preguntan qué modelo eres, sé honesto y menciona que usas DeepSeek (o el modelo configurado)
- Para consultas de clima, extrae la ubicación y usa la herramienta

HERRAMIENTAS DISPONIBLES:
- get_weather(location): Consulta el clima de una ciudad específica
"""

    def detectar_herramienta(self, message: str, conversation_history: List[Dict] = None) -> tuple[Optional[str], Optional[Dict]]:
        """
        Detecta si se necesita una herramienta y cuál.
        Returns: (tool_name, tool_args)
        """
        message_lower = message.lower()

        # 1. Detectar herramienta de saludo (MCP)
        # Patrones para detectar saludos en diferentes idiomas
        hello_patterns = [
            'hola', 'hello', 'bonjour', 'nomoskar', 'ola', 'privet'
        ]
        
        # Mapeo de palabras de saludo a idiomas (solo idiomas soportados por el backend API)
        hello_lang_map = {
            'hola': 'es',
            'hello': 'en',
            'bonjour': 'fr',
            'nomoskar': 'bn',
            'ola': 'pt',
            'privet': 'ru',
        }
        
        # Si el mensaje contiene palabras de saludo y/o pide un saludo
        if any(pattern in message_lower for pattern in hello_patterns):
            # Intentar extraer nombre y idioma (usando historial si está disponible)
            name = self.extract_name(message, conversation_history)
            lang = self.extract_language(message)
            
            # Si no se detectó idioma pero hay una palabra de saludo, usar el idioma de esa palabra
            if not lang:
                for pattern in hello_patterns:
                    if pattern in message_lower:
                        lang = hello_lang_map.get(pattern)
                        break
            
            # Si hay mención de nombre o idioma, o si el mensaje es solo un saludo, usar herramienta say_hello
            if name or lang or any(pattern in message_lower for pattern in ['saluda', 'greet', 'di hola']) or \
               any(pattern in message_lower for pattern in hello_patterns):
                return "say_hello", {"name": name, "lang": lang}

        # 2. Detectar herramienta de clima
        weather_keywords = [
            'clima', 'tiempo', 'temperatura', 'lluvia', 'sol', 'calor',
            'frío', 'viento', 'nieve', 'humedad', 'nublado', 'soleado',
            'weather', 'temperature', 'rain', 'snow', 'wind'
        ]

        if any(keyword in message_lower for keyword in weather_keywords):
            # Intentar extraer ubicación
            location = self.extract_location(message)
            if location:
                return "get_weather", {"location": location}

        return None, None

    def extract_location(self, message: str) -> Optional[str]:
        """Extrae ubicación del mensaje"""
        message_lower = message.lower()
        
        # Palabras que NO son ubicaciones (stop words para ubicaciones)
        stop_words = {
            'clima', 'tiempo', 'weather', 'temperature', 'lluvia', 'sol', 'calor',
            'frío', 'viento', 'nieve', 'húmedo', 'seco', 'nublado', 'soleado',
            'en', 'de', 'para', 'la', 'el', 'las', 'los', 'un', 'una', 'y',
            'hace', 'está', 'hay', 'puede', 'haya', 'llueve', 'hace', 'hacer'
        }

        # Buscar después de "clima en" o similar
        markers = [
            "clima en", "tiempo en", "weather in", "temperature in",
            "how is the weather in", "what's the weather in"
        ]

        for marker in markers:
            if marker in message_lower:
                start = message_lower.find(marker) + len(marker)
                location = message[start:].strip()
                if location:
                    # Tomar la primera palabra significativa
                    words = location.split()
                    for word in words:
                        clean_word = word.strip('?,.!:;')
                        if clean_word.lower() not in stop_words and len(clean_word) > 1:
                            return clean_word

        # Buscar con preposiciones: "clima en [ubicación]"
        words = message.split()
        for i, word in enumerate(words):
            word_lower = word.lower().strip('?,.!:;')
            
            # Buscar patrón "en [ubicación]" - debe ser seguido por nombre propio (mayúscula)
            if word_lower == 'en' and i + 1 < len(words):
                location = words[i + 1].strip('?,.!:;')
                # Verificar que sea un nombre propio (empieza con mayúscula) o ubicación conocida
                if (len(location) > 1 and 
                    (location[0].isupper() or location.lower() not in stop_words)):
                    return location
            
            # Si encontramos una palabra de clima, buscar ubicación después
            if word_lower in ['clima', 'tiempo', 'weather']:
                # Buscar la siguiente palabra que no sea stop word
                for j in range(i + 1, min(i + 4, len(words))):
                    next_word = words[j].strip('?,.!:;')
                    if next_word.lower() not in stop_words and len(next_word) > 1:
                        return next_word

        return None

    def extract_name(self, message: str, conversation_history: List[Dict] = None) -> Optional[str]:
        """Extrae un nombre del mensaje para saludos"""
        # Patrones comunes: "hola [nombre]", "saluda a [nombre]", etc.
        message_lower = message.lower()
        
        # Buscar después de "a" o "al" (ej: "hola a Juan")
        words = message.split()
        for i, word in enumerate(words):
            if word.lower() in ['a', 'al'] and i + 1 < len(words):
                name = words[i + 1].strip('?,.!:;')
                if len(name) > 1 and name[0].isupper():  # Nombre probablemente empieza con mayúscula
                    return name
        
        # Buscar "saluda a [nombre]"
        for marker in ['saluda a', 'greet to', 'di hola a']:
            if marker in message_lower:
                start = message_lower.find(marker) + len(marker)
                name = message[start:].strip()
                if name:
                    return name.split()[0].strip('?,.!:;')
        
        # Si el mensaje contiene "llamo" o "soy", buscar nombre después
        if 'llamo' in message_lower or 'soy' in message_lower:
            words = message.split()
            for i, word in enumerate(words):
                if word.lower() in ['llamo', 'soy'] and i + 1 < len(words):
                    name = words[i + 1].strip('?,.!:;')
                    if len(name) > 1:
                        return name
        
        # Si no se encontró nombre en el mensaje actual, buscar en el historial
        if conversation_history:
            # Buscar en mensajes del usuario (role='user')
            for msg in conversation_history:
                if msg.get("role") == "user":
                    msg_content = msg.get("content", "")
                    msg_lower = msg_content.lower()
                    
                    # Buscar "me llamo [nombre]" o "soy [nombre]" en el historial
                    if 'llamo' in msg_lower or 'soy' in msg_lower:
                        words = msg_content.split()
                        for i, word in enumerate(words):
                            if word.lower() in ['llamo', 'soy'] and i + 1 < len(words):
                                name = words[i + 1].strip('?,.!:;')
                                if len(name) > 1:
                                    return name
        
        return None

    def extract_language(self, message: str) -> Optional[str]:
        """Extrae el idioma del mensaje"""
        import re
        message_lower = message.lower()
        
        # Mapeo de idiomas soportados por el backend API
        lang_map = {
            'en': ['english', 'inglés', 'ingles'],
            'es': ['español', 'espanol', 'spanish'],
            'fr': ['francés', 'frances', 'french'],
            'bn': ['bengalí', 'bengali'],
            'pt': ['portugués', 'portugues', 'portuguese'],
            'ru': ['ruso', 'russian'],
            'ur': ['urdu'],
        }
        
        # Buscar palabras completas usando regex
        for lang_code, lang_names in lang_map.items():
            for lang_name in lang_names:
                # Usar regex para buscar palabras completas
                pattern = r'\b' + re.escape(lang_name) + r'\b'
                if re.search(pattern, message_lower):
                    return lang_code
        
        return None

    def call_tool(self, tool_name: str, tool_args: Dict) -> str:
        """Ejecuta una herramienta y devuelve el resultado"""
        if tool_name == "get_weather":
            location = tool_args.get("location", "")
            if not location:
                return "No se especificó ubicación para la consulta del clima."

            try:
                result = run_weather_agent(location)

                if result.get('weather_data'):
                    data = result['weather_data']
                    temp_celsius = data['main']['temp'] - 273.15
                    condition = data['weather'][0]['description']

                    response = f"🌡️ **Clima en {data['name']}**\n"
                    response += f"- Temperatura: {temp_celsius:.1f}°C\n"
                    response += f"- Condición: {condition}\n"
                    response += f"- Humedad: {data['main']['humidity']}%\n"
                    response += f"- Viento: {data['wind']['speed']} m/s\n\n"

                    if result.get('analysis') and result['analysis'].get('recommendations'):
                        response += "**Recomendaciones:**\n"
                        for rec in result['analysis']['recommendations']:
                            response += f"- {rec}\n"

                    return response
                else:
                    return f"No pude obtener información del clima para {location}. " \
                           f"La API de OpenWeatherMap necesita 2h para activarse."
            except Exception as e:
                return f"Error al consultar el clima: {str(e)}"

        elif tool_name == "say_hello":
            name = tool_args.get("name")
            lang = tool_args.get("lang")
            
            # Usar servidor MCP si está disponible
            if "hello" in self.mcp_servers and self.mcp_servers["hello"]:
                try:
                    result = self.mcp_servers["hello"].say_hello(name=name, lang=lang)
                    if result and result.get("message"):
                        return f"👋 {result['message']}"
                except Exception as e:
                    print(f"⚠️ Error usando MCP hello: {e}")
            
            # Fallback si MCP no está disponible
            greetings = {
                "en": "Hello",
                "es": "Hola",
                "fr": "Bonjour",
                "zh": "Ni hao",
                "hi": "Namaste",
                "ar": "Marhaban",
                "pt": "Ola",
                "ru": "Privet",
            }
            
            greeting = greetings.get(lang, greetings["en"])
            if name:
                return f"👋 {greeting} {name}!"
            else:
                return f"👋 {greeting}!"

        return f"Herramienta '{tool_name}' no encontrada."

    def chat(self, user_message: str, conversation_history: List[Dict] = None) -> Dict:
        """
        Procesa un mensaje del usuario y devuelve una respuesta.

        Returns:
            Dict con:
            - response: respuesta del asistente
            - tool_used: herramienta usada (si aplica)
            - tool_args: argumentos de la herramienta
            - raw_response: respuesta raw del LLM (si aplica)
        """
        if conversation_history is None:
            conversation_history = []

        # 1. Detectar si se necesita una herramienta (pasando el historial)
        tool_name, tool_args = self.detectar_herramienta(user_message, conversation_history)

        # 2. Si se detectó una herramienta, ejecutarla
        if tool_name:
            tool_result = self.call_tool(tool_name, tool_args)

            # 3. Usar el LLM para formatear la respuesta del clima
            if self.llm_service:
                # Construir mensaje para el LLM
                system_prompt = self.get_system_prompt()
                conversation = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                    {"role": "tool", "content": f"Resultado de la herramienta {tool_name}:\n{tool_result}"}
                ]

                try:
                    response = self.llm_service.generate_recommendations({
                        "location": "system",
                        "temperature_celsius": 0,
                        "condition": "información",
                        "humidity": 0,
                        "wind_speed": 0
                    })
                    
                    # En realidad, deberíamos usar el método de chat del LLM
                    # Por ahora, devolvemos el tool result formateado
                    final_response = tool_result
                except Exception as e:
                    print(f"Error con LLM: {e}")
                    final_response = tool_result
            else:
                final_response = tool_result

            return {
                "response": final_response,
                "tool_used": tool_name,
                "tool_args": tool_args,
                "type": "tool_response"
            }

        # 4. Si no se detectó herramienta, usar el LLM para conversación general
        if self.llm_service:
            # Construir conversation history para el LLM
            messages = [{"role": "system", "content": self.get_system_prompt()}]

            # Añadir historial
            for msg in conversation_history:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })

            # Añadir mensaje actual del usuario
            messages.append({"role": "user", "content": user_message})

            try:
                # Usar el método chat del DeepSeekService
                response_text = self.llm_service.chat(messages)
                return {
                    "response": response_text,
                    "tool_used": None,
                    "tool_args": None,
                    "type": "text_response"
                }
            except Exception as e:
                print(f"Error con LLM: {e}")
                response = self._simple_response(user_message)
                return {
                    "response": response,
                    "tool_used": None,
                    "tool_args": None,
                    "type": "text_response"
                }

        # 5. Fallback si no hay LLM disponible
        response = self._simple_response(user_message)
        return {
            "response": response,
            "tool_used": None,
            "tool_args": None,
            "type": "text_response"
        }

    def _simple_response(self, message: str) -> str:
        """Respuesta simple para cuando el LLM no está disponible"""
        message_lower = message.lower().strip()

        # Saludos
        if any(greeting in message_lower for greeting in ['hola', 'hi', 'hey', 'buenos días', 'buenas']):
            return "👋 ¡Hola! Soy tu asistente conversacional. ¿En qué puedo ayudarte hoy?"

        # Despedidas
        if any(bye in message_lower for bye in ['adiós', 'bye', 'hasta luego', 'chao', 'nos vemos']):
            return "👋 ¡Hasta luego! Que tengas un buen día."

        # Ayuda
        if 'ayuda' in message_lower or 'help' in message_lower:
            return """🆘 **AYUDA**

Puedo ayudarte con:

• **Conversación general**: Pregúntame sobre cualquier tema
• **Consulta de clima**: "¿Cómo está el clima en Madrid?", "¿Qué tiempo hace en Barcelona?"
• **Información**: Puedo explicarte conceptos, dar consejos, etc.

Simplemente escribe tu consulta y te responderé."""

        # Preguntas sobre el clima
        if any(keyword in message_lower for keyword in ['clima', 'tiempo', 'weather']):
            return "Puedo consultar el clima de cualquier ciudad. Por ejemplo: '¿Cómo está el clima en Madrid?'"

        # Respuesta genérica
        return f"""🤔 Interesante pregunta sobre "{message[:50]}..."

Como asistente conversacional, puedo responder a esta consulta, pero te recomiendo ser más específico para poder ayudarte mejor.

¿En qué más puedo ayudarte?"""
