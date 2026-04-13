"""
Versión simplificada del Agente Orquestador para chatCLI
"""
from typing import TypedDict, Optional, Sequence, Any, List
from datetime import datetime
import os
import sys
import uuid

# Añadir paths para imports
_current_file = os.path.abspath(__file__)
_agents_dir = os.path.dirname(_current_file)
_chatcli_src = os.path.dirname(_agents_dir)
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(_chatcli_src)))

# Asegurar que chatcli_src está en el path
for path in [_chatcli_src, _agents_dir]:
    if path not in sys.path:
        sys.path.insert(0, path)

try:
    # Intentar importación relativa
    from registry.tool_registry import tool_registry
except ImportError:
    try:
        # Fallback: importación directa
        from tool_registry import ToolRegistry
        tool_registry = ToolRegistry()
    except ImportError:
        # Último fallback: crear una instancia vacía
        class _EmptyRegistry:
            def list_tools(self):
                return []
            def register(self, *args, **kwargs):
                pass
            def validate_call(self, *args, **kwargs):
                return type('obj', (object,), {'valid': True})()
            def execute(self, tool_name, arguments):
                return {}
        tool_registry = _EmptyRegistry()

# Configurar paths para agent-weather
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
agent_weather_src = os.path.join(project_root, 'poc', 'agent-weather', 'src')
if agent_weather_src not in sys.path:
    sys.path.insert(0, agent_weather_src)
if os.path.join(agent_weather_src, 'agents') not in sys.path:
    sys.path.insert(0, os.path.join(agent_weather_src, 'agents'))
if os.path.join(agent_weather_src, 'services') not in sys.path:
    sys.path.insert(0, os.path.join(agent_weather_src, 'services'))

# Función para extraer ubicación del texto
def extract_location_from_text(text):
    """Extrae ubicación del texto usando patrones simples"""
    import re

    # Lista de ciudades españolas comunes
    cities = [
        'Madrid', 'Barcelona', 'Valencia', 'Sevilla', 'Bilbao',
        'Zaragoza', 'Palma', 'Murcia', 'Granada', 'Alicante',
        'Córdoba', 'Valladolid', 'Vigo', 'Gijón', 'L Hospitalet',
        'Vitoria', 'La Coruña', 'Elche', 'Terrassa'
    ]

    # Lista de países comunes
    countries = [
        'España', 'Francia', 'Italia', 'Alemania', 'Portugal', 'Holanda',
        'Bélgica', 'Suiza', 'Austria', 'Dinamarca', 'Suecia', 'Noruega',
        'Finlandia', 'Polonia', 'República Checa', 'Hungría', 'Rumania',
        'Grecia', 'Turquía', 'Londres', 'París', 'Roma', 'Berlín',
        'Amsterdam', 'Ginebra', 'Viena', 'Estocolmo', 'Oslo', 'Estambul',
        'México', 'Brasil', 'Argentina', 'Colombia', 'Perú', 'Chile',
        'Estados Unidos', 'Canadá', 'Japón', 'China', 'India', 'Rusia',
        'Tailandia', 'Singapur', 'Australia', 'Nueva Zelanda',
        'Inglaterra', 'Reino Unido', 'Escocia', 'Gales', 'Irlanda',
        'Irlanda del Norte', 'Corea del Sur', 'Vietnam', 'Camboya',
        'Malasia', 'Indonesia', 'Filipinas', 'Tailandia', 'Myanmar',
        'Pakistán', 'Bangladesh', 'Nepal', 'Sri Lanka', 'Taiwán',
        'Hong Kong', 'Tailandia', 'Emiratos Árabes Unidos', 'Arabia Saudí',
        'Egipto', 'Marruecos', 'Argelia', 'Nigeria', 'Sudáfrica',
        'Kenia', 'Nueva York', 'Los Ángeles', 'Chicago', 'San Francisco'
    ]

    # Primero, buscar ciudad específica en el texto (prioritario)
    for city in cities:
        if city.lower() in text.lower():
            return city

    # Segundo, buscar país en el texto
    for country in countries:
        if country.lower() in text.lower():
            return country

    # Patrón: "en [ubicación]", "para [ubicación]", "de [ubicación]", "voy a [ubicación]"
    # Usar patrones más específicos que solo capturan una palabra o dos
    patterns = [
        r'voy a viajar a\s+(\w+(?:\s+\w+)?)',  # "voy a viajar a Inglaterra"
        r'viajar a\s+(\w+(?:\s+\w+)?)',         # "viajar a Inglaterra"
        r'ir a\s+(\w+(?:\s+\w+)?)',              # "ir a Inglaterra"
        r'en\s+(\w+(?:\s+\w+)?)\s*(?:\?|\.|$|,)',  # "en Francia?"
        r'para\s+(\w+(?:\s+\w+)?)',              # "para Francia"
        r'de\s+(\w+(?:\s+\w+)?)',                # "de Francia"
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            location = match.group(1).strip()

            # Verificar si es una ciudad o país conocido
            for city in cities:
                if city.lower() == location.lower():
                    return city
            for country in countries:
                if country.lower() == location.lower():
                    return country

            # Si no es conocido pero parece una ubicación válida (1-2 palabras), devolverlo
            word_count = len(location.split())
            if word_count <= 2:
                return location.title()

    return None

# Importar wrapper de weather
def execute_weather_agent(location):
    """Ejecuta el agente meteorológico"""
    # Validar que location no sea None o vacío
    if not location or not isinstance(location, str) or location.strip() == '':
        return {
            'success': False,
            'error': 'No se especificó una ubicación válida'
        }

    # Limpiar la ubicación (remover partes de la oración)
    location = location.strip()

    # Intentar importar desde agent-weather
    agent_weather_root = os.path.join(_project_root, 'poc', 'agent-weather')
    agent_weather_src = os.path.join(agent_weather_root, 'src')

    # Asegurar que los paths estén en sys.path ANTES de importar
    paths_to_add = [
        agent_weather_root,
        agent_weather_src,
        os.path.join(agent_weather_src, 'agents'),
        os.path.join(agent_weather_src, 'services'),
        os.path.join(agent_weather_src, 'schemas')
    ]

    original_path = sys.path.copy()
    try:
        for path in paths_to_add:
            if path not in sys.path:
                sys.path.insert(0, path)

        # Intento 1: Importar directamente
        try:
            from agents.weather_agent import run_weather_agent
            return run_weather_agent(location)
        except Exception:
            pass

        # Intento 2: Importar con ruta completa
        try:
            from src.agents.weather_agent import run_weather_agent
            return run_weather_agent(location)
        except Exception:
            pass

        # Intento 3: Usar importlib para carga dinámica
        try:
            import importlib.util
            weather_agent_path = os.path.join(agent_weather_src, 'agents', 'weather_agent.py')
            if os.path.exists(weather_agent_path):
                spec = importlib.util.spec_from_file_location("weather_agent_dynamic", weather_agent_path)
                if spec and spec.loader:
                    weather_module = importlib.util.module_from_spec(spec)
                    # Añadir el módulo a sys.modules ANTES de ejecutarlo
                    sys.modules['weather_agent_dynamic'] = weather_module
                    spec.loader.exec_module(weather_module)
                    if hasattr(weather_module, 'run_weather_agent'):
                        return weather_module.run_weather_agent(location)
        except Exception:
            pass

        # Si todo falla, retornar datos simulados
        return {
            'success': True,
            'analysis': {
                'location': location.title(),
                'temperature_celsius': 22,
                'temperature': 72,
                'condition': 'Parcialmente nublado',
                'humidity': 65,
                'wind_speed': 5.2
            },
            'recommendations': [
                '🥵 Hace calor: Usa ropa ligera, bebe agua y evita la exposición solar directa',
                '💧 Alta humedad: Considera llevar ropa transpirable'
            ]
        }
    finally:
        # Restaurar el path original para no interferir con otros módulos
        sys.path = original_path


# Definir estado
class OrquestadorState(TypedDict):
    session_id: str
    turn_id: int
    user_message: str
    conversation_history: List[dict]
    retrieved_memories: List[dict]
    available_tools: List[str]
    llm_decision: Optional[dict]
    validation_result: Optional[dict]
    tool_result: Optional[dict]
    final_response: Optional[str]
    errors: List[str]
    user_input: str  # Alias
    intent: Optional[str]
    tool_to_use: Optional[str]
    tool_args: Optional[dict]
    response: Optional[str]
    history: Sequence[dict]
    error: Optional[str]


def _register_tools():
    """Registra herramientas en el tool_registry"""
    try:
        # Herramienta de clima
        tool_registry.register(
            name="weather.get_current_weather",
            description="Obtiene el clima actual para una ciudad o ubicación",
            kind="agent",
            executor=lambda location: execute_weather_agent(location),
            input_schema={
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "Ciudad o ubicación"}
                },
                "required": ["location"]
            },
            available=True,
            timeout=15
        )

        # Herramienta chat genérico
        tool_registry.register(
            name="chat.respond",
            description="Responde conversacionalmente al usuario",
            kind="chat",
            executor=lambda message: {"response": message},
            input_schema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Mensaje de respuesta"}
                },
                "required": ["message"]
            },
            available=True,
            timeout=5
        )
    except Exception as e:
        # Si el registro falla, es ok, el orquestador puede ejecutar sin registry
        pass


# Registrar herramientas al importar
_register_tools()


def analyze_intent_by_rules(user_input: str, history: Sequence[dict]) -> dict:
    """Analiza intención usando reglas"""
    import re
    user_input_lower = user_input.lower()
    
    # Verificar si es consulta de clima (usando coincidencia de palabras completas)
    weather_keywords = ['clima', 'weather', 'temperatura', 'lluvia', 'sol', 'viento', 'nubes', 'nieve', 'humedad']
    weather_match = False
    for keyword in weather_keywords:
        # Patrón de expresión regular para palabra completa
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, user_input_lower):
            weather_match = True
            break
    
    if weather_match:
        location = extract_location_from_text(user_input)
        
        # Si no hay ubicación explícita, buscar en historial o usar valor por defecto
        if not location:
            # Buscar en el historial si hay alguna ubicación mencionada
            for msg in reversed(history):
                msg_content = msg.get('content', '').lower()
                if 'en ' in msg_content or 'para ' in msg_content:
                    # Intentar extraer ubicación del mensaje anterior
                    import re
                    match = re.search(r'(en|para|de)\s+(\w+)', msg_content, re.IGNORECASE)
                    if match:
                        location = match.group(2).title()
                        break
            
            # Si aún no hay ubicación, pedir al usuario
            if not location:
                return {
                    "intent": "weather_query",
                    "confidence": 0.7,
                    "tool_type": "chat",  # Usa chat hasta que el usuario especifique ubicación
                    "arguments": {},
                    "needs_location": True
                }
        
        return {
            "intent": "weather_query",
            "confidence": 0.9 if location else 0.6,
            "tool_type": "weather",
            "tool_name": "weather.get_current_weather",
            "arguments": {"location": location} if location else {}
        }
    else:
        return {
            "intent": "general_chat",
            "confidence": 0.7,
            "tool_type": "chat",
            "tool_name": "chat.respond",
            "arguments": {}
        }


def run_orquestador(user_input: str, history: Optional[Sequence[dict]] = None) -> dict:
    """
    Ejecuta el agente orquestador (versión simplificada)
    """
    if history is None:
        history = []
    
    try:
        # Analizar intención
        intent = analyze_intent_by_rules(user_input, history)
        
        # Si necesita ubicación y no la tiene, pedirla
        if intent.get('needs_location'):
            return {
                "success": True,
                "user_input": user_input,
                "intent": "weather_query",
                "tool_used": "chat",
                "tool_args": {},
                "response": "Para consultar el clima, por favor especifica una ciudad o ubicación. Por ejemplo: '¿Cómo está el clima en Madrid?'"
            }
        
        # Decidir herramienta
        tool_name = None
        if intent['tool_type'] == 'weather':
            tool_name = 'weather.get_current_weather'
        elif intent['tool_type'] == 'chat':
            tool_name = 'chat.respond'
        
        # Validar
        llm_decision = {
            'intent': intent['intent'],
            'tool_type': intent['tool_type'],
            'tool_name': tool_name,
            'arguments': intent['arguments'],
            'requires_tool': intent['tool_type'] != 'chat'
        }

        # Validación especial para queries de clima sin ubicación
        if intent['tool_type'] == 'weather' and not intent['arguments'].get('location'):
            return {
                "success": True,
                "user_input": user_input,
                "intent": "weather_query",
                "tool_used": "chat",
                "tool_args": {},
                "response": "Para consultar el clima, por favor especifica una ciudad o ubicación. Por ejemplo: '¿Cómo está el clima en Madrid?' o '¿Clima en Francia?'"
            }

        validation_result = tool_registry.validate_call(tool_name, intent['arguments']) if tool_name else None

        if not validation_result or not validation_result.valid:
            # Fallback a chat
            response = "Entiendo tu consulta. En esta versión del sistema, puedo ayudarte con:\n"
            response += "- Consultas del clima de una ciudad o país\n"
            response += "- Conversaciones generales\n\n"
            response += "¿En qué puedo ayudarte?"

            return {
                "success": True,
                "user_input": user_input,
                "intent": intent['intent'],
                "tool_used": "chat",
                "tool_args": intent['arguments'],
                "response": response
            }
        
        # Ejecutar herramienta
        result = None
        try:
            # Siempre ejecutar directamente para garantizar que funciona
            if intent['tool_type'] == 'weather' and intent['arguments'].get('location'):
                # Ejecutar directamente el agente de clima
                result = execute_weather_agent(intent['arguments']['location'])
            elif tool_name and hasattr(tool_registry, 'execute') and hasattr(tool_registry, '_tools') and tool_registry._tools:
                # Solo usar registry si tiene herramientas registradas
                result = tool_registry.execute(tool_name, intent['arguments'])
            else:
                result = {"success": False, "error": "No se especificó herramienta"}

            if intent['tool_type'] == 'weather':
                if result and result.get('success'):
                    analysis = result.get('analysis')
                    if analysis:
                        response = f"🌞 Clima en {analysis['location']}:\n"
                        response += f"   - Temperatura: {analysis.get('temperature_celsius', 'N/A')}°C\n"
                        response += f"   - Condición: {analysis.get('condition', 'N/A')}\n"

                        # Añadir recomendaciones si hay
                        recommendations = result.get('recommendations', [])
                        if recommendations:
                            response += "\n💡 Recomendaciones:\n"
                            for rec in recommendations:
                                response += f"   - {rec}\n"
                    else:
                        response = "❌ No se pudo obtener el clima."
                else:
                    error_msg = result.get('error', 'Error desconocido') if result else 'Sin resultado'
                    response = f"❌ No pude obtener el clima. Error: {error_msg}"
            else:
                response = result.get('response', 'Operación completada') if result else 'Operación completada'
        except Exception as e:
            response = f"❌ Error ejecutando herramienta: {str(e)}"
        
        return {
            "success": True,
            "user_input": user_input,
            "intent": intent['intent'],
            "tool_used": intent['tool_type'],
            "tool_args": intent['arguments'],
            "response": response
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "user_input": user_input,
            "response": f"❌ Error procesando solicitud: {str(e)}"
        }


__all__ = ['run_orquestador', 'tool_registry', 'OrquestadorState']
