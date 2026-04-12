"""
Agente Orquestador con LangGraph
Decide qué herramienta usar según la intención del usuario usando LLM
"""
from typing import TypedDict, Annotated, Sequence, Optional, Literal, Any, List
from langgraph.graph import StateGraph, END, START
from langgraph.graph.state import CompiledStateGraph
from datetime import datetime
import re
import json
import sys
import os
import tomli
import uuid
import time

# Calcular rutas ANTES de cualquier importación
current_dir = os.path.dirname(os.path.abspath(__file__))
agent_orquestador_src = os.path.dirname(current_dir)  # poc/agent-orquestador/src
project_root = os.path.dirname(os.path.dirname(agent_orquestador_src))  # agentes-con-LangGraph

# Añadir TODOS los paths necesarios ANTES de importar
paths_to_add = [
    agent_orquestador_src,
    project_root,
    os.path.join(project_root, 'poc', 'agent-weather', 'src'),
    os.path.join(project_root, 'poc', 'agent-weather', 'src', 'agents'),
    os.path.join(project_root, 'poc', 'agent-weather', 'src', 'services'),
    os.path.join(project_root, 'poc', 'agent-weather', 'src', 'schemas'),
    os.path.join(project_root, 'poc', 'agent-weather'),
    os.path.join(project_root, 'lib'),
    os.path.join(agent_orquestador_src, 'schemas'),
    os.path.join(agent_orquestador_src, 'services'),
    os.path.join(agent_orquestador_src, 'registry'),
    os.path.join(agent_orquestador_src, 'validators'),
]

for path in paths_to_add:
    if path not in sys.path:
        sys.path.insert(0, path)

try:
    from src.schemas.orquestador import OrquestadorState, IntentAnalysis, ToolExecutionResult, ToolType
    from src.services.weather_agent_wrapper import execute_weather_agent, extract_location_from_text
    from src.services.mcp_wrapper import execute_mcp_tool, list_mcp_tools
    from src.registry.tool_registry import tool_registry
    from src.validators.decision_validator import DecisionValidator
    from src.services.logger import logger
except ImportError:
    try:
        from schemas.orquestador import OrquestadorState, IntentAnalysis, ToolExecutionResult, ToolType
        from services.weather_agent_wrapper import execute_weather_agent, extract_location_from_text
        from services.mcp_wrapper import execute_mcp_tool, list_mcp_tools
        from registry.tool_registry import tool_registry
        from validators.decision_validator import DecisionValidator
        from services.logger import logger
    except ImportError:
        try:
            # Fallback para ejecución directa
            from orquestador import OrquestadorState, IntentAnalysis, ToolExecutionResult, ToolType
            from weather_agent_wrapper import execute_weather_agent, extract_location_from_text
            from mcp_wrapper import execute_mcp_tool, list_mcp_tools
            from tool_registry import tool_registry
            from decision_validator import DecisionValidator
            from logger import logger
        except ImportError as e:
            raise ImportError(f"No se pudo importar los módulos necesarios: {e}")


def _register_tools():
    """Registra todas las herramientas en el tool_registry"""
    
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
        output_schema={
            "type": "object",
            "properties": {
                "location": {"type": "string"},
                "temperature": {"type": "number"},
                "condition": {"type": "string"}
            }
        },
        available=True,
        timeout=15
    )
    
    # Herramienta MCP de saludo
    tool_registry.register(
        name="mcp.say_hello",
        description="Saluda personalizado en diferentes idiomas",
        kind="mcp",
        executor=lambda name, lang: execute_mcp_tool("say_hello", {"name": name, "lang": lang}),
        input_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Nombre de la persona"},
                "lang": {"type": "string", "description": "Idioma (es, en, fr, etc.)"}
            },
            "required": ["name", "lang"]
        },
        available=True,
        timeout=5
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


# Registrar herramientas al importar el módulo
_register_tools()


class AgentOrquestador:
    """Clase principal del agente orquestador con LLM"""
    
    def __init__(self):
        # Añadir paths del agente meteorológico para DeepSeek
        agent_weather_root = os.path.join(project_root, 'poc', 'agent-weather')
        agent_weather_src = os.path.join(agent_weather_root, 'src')
        
        paths_to_add = [
            agent_weather_root,
            agent_weather_src,
            os.path.join(agent_weather_src, 'services'),
            os.path.join(agent_weather_src, 'schemas'),
            project_root,
        ]
        
        for path in paths_to_add:
            if path not in sys.path:
                sys.path.insert(0, path)
        
        # Inicializar cliente DeepSeek
        self.llm_available = False
        try:
            from deepseek_service import LLMProviderService
            self.llm = LLMProviderService()
            self.llm_available = True
        except Exception as e:
            print(f"⚠️  DeepSeek no disponible ({e}), usando análisis por reglas")
        
        # Listar herramientas MCP disponibles
        try:
            self.mcp_tools = list_mcp_tools()
            self.mcp_tool_names = [tool['name'] for tool in self.mcp_tools]
        except:
            self.mcp_tools = []
            self.mcp_tool_names = ['say_hello', 'get_hello_languages']
        
        # Definir palabras clave
        self.weather_keywords = [
            'clima', 'weather', 'temperatura', ' temperatura', 'lluvia', 'rain',
            'sol', 'sun', 'viento', 'wind', 'humedad', 'humidity', 'nieve', 'snow',
            'nubes', 'clouds', 'amanecer', 'atardecer', 'predicción', 'forecast',
            'tiempo', 'hace', 'hoy', 'mañana'
        ]
        
        self.mcp_keywords = [
            'hola', 'hello', 'saludar', 'greet', 'idioma', 'language',
            'herramienta', 'tool', 'mcp', 'servicio', 'service',
            'saluda', 'decir', 'hablar'
        ]
    
    def analyze_intent_by_rules(self, user_input: str, history: Sequence[dict[str, str]]) -> IntentAnalysis:
        """
        Analiza la intención del usuario usando reglas (fallback del LLM)
        """
        user_input_lower = user_input.lower()
        
        # Verificar si es consulta de clima
        weather_match = any(keyword in user_input_lower for keyword in self.weather_keywords)
        
        # Verificar si es comando MCP
        mcp_match = any(keyword in user_input_lower for keyword in self.mcp_keywords)
        
        # Verificar si es un comando MCP directo
        mcp_direct_command = user_input.strip().startswith(tuple(self.mcp_tool_names))
        
        # Determinar herramienta a usar
        if weather_match:
            tool_type: ToolType = "weather"
            location = extract_location_from_text(user_input)
            
            # Si no hay ubicación, buscar en historial
            if not location and history:
                for msg in reversed(history):
                    if 'vive en' in msg.get('content', '').lower():
                        match = re.search(r'vive en\s+(\w+)', msg['content'].lower())
                        if match:
                            location = match.group(1).title()
                            break
            
            arguments = {"location": location} if location else {}
            
            return {
                "intent": "weather_query",
                "confidence": 0.9 if location else 0.6,
                "tool_type": tool_type,
                "arguments": arguments
            }
        
        elif mcp_direct_command or mcp_match:
            tool_type: ToolType = "mcp"
            
            # Extraer nombre de herramienta y argumentos
            if mcp_direct_command:
                # Formato: say_hello(name=Juan, lang=es)
                match = re.match(r'(\w+)\((.*)\)', user_input.strip())
                if match:
                    tool_name = match.group(1)
                    args_str = match.group(2)
                    
                    # Parsear argumentos
                    arguments = {}
                    for part in args_str.split(','):
                        if '=' in part:
                            key, value = part.split('=', 1)
                            arguments[key.strip()] = value.strip().strip("'\"")
                    
                    return {
                        "intent": f"mcp_{tool_name}",
                        "confidence": 0.95,
                        "tool_type": tool_type,
                        "arguments": {"tool_name": tool_name, **arguments}
                    }
            
            # Saludo genérico
            return {
                "intent": "mcp_greet",
                "confidence": 0.8,
                "tool_type": tool_type,
                "arguments": {"tool_name": "say_hello"}
            }
        
        else:
            # Por defecto, usar chat genérico
            tool_type: ToolType = "chat"
            return {
                "intent": "general_chat",
                "confidence": 0.7,
                "tool_type": tool_type,
                "arguments": {}
            }
    
    def analyze_intent(self, user_input: str, history: Sequence[dict[str, str]]) -> IntentAnalysis:
        """
        Analiza la intención del usuario (con LLM si está disponible)
        """
        if self.llm_available:
            return self.analyze_intent_with_llm(user_input, history)
        else:
            return self.analyze_intent_by_rules(user_input, history)
    
    def analyze_intent_with_llm(self, user_input: str, history: Sequence[dict[str, str]]) -> IntentAnalysis:
        """
        Analiza la intención del usuario usando LLM
        """
        # Construir mensajes para el LLM
        messages = []
        
        # Añadir historial
        for msg in history[-5:]:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
        
        # Cargar prompt base desde TOML
        config_path = os.path.join(project_root, 'agent-orquestador', 'config', 'prompts.toml')
        try:
            with open(config_path, 'rb') as f:
                config = tomli.load(f)
                base_prompt = config['system_prompt']['content']
        except Exception as e:
            print(f"⚠️  No se pudo cargar prompts.toml: {e}")
            # Fallback al prompt original
            base_prompt = """Eres un asistente inteligente que analiza la intención del usuario y decide qué herramienta usar."""
        
        # Obtener herramientas disponibles del registry
        tools_description = tool_registry.get_tools_prompt_description()
        
        # Construir sistema de prompt
        system_prompt = base_prompt.format(
            available_tools=tools_description,
            mcp_tools_details="\n".join([f"- {name}" for name in self.mcp_tool_names])
        )
        
        messages.insert(0, {"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_input})
        
        try:
            response = self.llm.chat(messages)
            
            # Parsear respuesta JSON
            parsed, error = DecisionValidator.parse_llm_response(response)
            
            if parsed and not error:
                # Validar y normalizar la decisión
                validated = DecisionValidator.sanitize_llm_decision(parsed)
                
                return {
                    "intent": validated.get("intent", "general_chat"),
                    "confidence": validated.get("confidence", 0.7),
                    "tool_type": validated.get("tool_type", "chat"),
                    "arguments": validated.get("arguments", {})
                }
            else:
                # Si hay error, usar análisis por reglas
                return self.analyze_intent_by_rules(user_input, history)
                
        except Exception:
            return self.analyze_intent_by_rules(user_input, history)
    
    def execute_tool(self, intent: IntentAnalysis) -> ToolExecutionResult:
        """
        Ejecuta la herramienta determinada por el análisis de intención
        """
        tool_type = intent['tool_type']
        
        if tool_type == "weather":
            location = intent['arguments'].get('location')
            
            if not location:
                return {
                    "success": False,
                    "tool_used": "weather",
                    "tool_args": intent['arguments'],
                    "response": "Por favor, especifica una ubicación para consultar el clima.",
                    "timestamp": datetime.now()
                }
            
            result = execute_weather_agent(location)
            
            if result['success']:
                analysis = result['analysis']
                recommendations = result['recommendations']
                
                if analysis is None:
                    return {
                        "success": False,
                        "tool_used": "weather",
                        "tool_args": intent['arguments'],
                        "response": f"❌ No se pudieron obtener datos climáticos para {location}",
                        "timestamp": datetime.now()
                    }
                
                response_text = f"🌞 Clima en {analysis['location']}:\n"
                response_text += f"   - Temperatura: {analysis['temperature_celsius']}°C ({analysis['temperature']}°F)\n"
                response_text += f"   - Condición: {analysis['condition']}\n"
                response_text += f"   - Humedad: {analysis['humidity']}%\n"
                response_text += f"   - Viento: {analysis['wind_speed']} m/s\n\n"
                response_text += "💡 Recomendaciones:\n"
                for rec in recommendations:
                    response_text += f"   - {rec}\n"
                
                return {
                    "success": True,
                    "tool_used": "weather",
                    "tool_args": intent['arguments'],
                    "response": response_text,
                    "timestamp": datetime.now()
                }
            else:
                return {
                    "success": False,
                    "tool_used": "weather",
                    "tool_args": intent['arguments'],
                    "response": f"❌ No pude obtener el clima. Error: {result.get('error', 'Desconocido')}",
                    "timestamp": datetime.now()
                }
        
        elif tool_type == "mcp":
            tool_name = intent['arguments'].get('tool_name', 'say_hello')
            args = {k: v for k, v in intent['arguments'].items() if k != 'tool_name'}
            
            result = execute_mcp_tool(tool_name, args)
            
            if result['success']:
                return {
                    "success": True,
                    "tool_used": "mcp",
                    "tool_args": intent['arguments'],
                    "response": result['response'],
                    "timestamp": datetime.now()
                }
            else:
                return {
                    "success": False,
                    "tool_used": "mcp",
                    "tool_args": intent['arguments'],
                    "response": f"❌ Error ejecutando herramienta MCP: {result.get('error', 'Desconocido')}",
                    "timestamp": datetime.now()
                }
        
        else:
            # Chat genérico con LLM
            return {
                "success": True,
                "tool_used": "chat",
                "tool_args": intent['arguments'],
                "response": "Estoy aquí para ayudarte. Puedo consultar el clima, saludarte en diferentes idiomas, o conversar sobre otros temas.",
                "timestamp": datetime.now()
            }


# ==================== LANGGRAPH NODOS ====================

def load_context_node(state: OrquestadorState) -> OrquestadorState:
    """Nodo: Carga contexto inicial y configura el estado"""
    new_state = dict(state)
    
    # Inicializar session_id y turn_id si no existen
    if 'session_id' not in new_state or not new_state['session_id']:
        new_state['session_id'] = str(uuid.uuid4())[:8]
    
    if 'turn_id' not in new_state:
        new_state['turn_id'] = 1
    else:
        new_state['turn_id'] = new_state['turn_id'] + 1
    
    # Inicializar campos si no existen
    new_state.setdefault('conversation_history', [])
    new_state.setdefault('retrieved_memories', [])
    new_state.setdefault('available_tools', [])
    new_state.setdefault('errors', [])
    
    # Actualizar campos heredados para compatibilidad
    new_state['user_input'] = new_state.get('user_message', new_state.get('user_input', ''))
    
    return new_state


def retrieve_memory_node(state: OrquestadorState) -> OrquestadorState:
    """Nodo: Recupera memoria semántica relevante desde FAISS"""
    # En una implementación real, esto consultaría FAISS
    # Por ahora, simulamos recuperación vacía
    new_state = dict(state)
    new_state['retrieved_memories'] = []
    
    return new_state


def analyze_intent_node(state: OrquestadorState) -> OrquestadorState:
    """Nodo: Analiza intención del usuario"""
    orquestador = AgentOrquestador()
    
    user_message = state.get('user_message', state.get('user_input', ''))
    history = state.get('conversation_history', [])
    session_id = state.get('session_id', 'unknown')
    turn_id = state.get('turn_id', 0)
    
    # Medir tiempo de análisis
    start_time = time.time()
    intent = orquestador.analyze_intent(user_message, history)
    latency_ms = (time.time() - start_time) * 1000
    
    # Convertir IntentAnalysis a dict para el estado
    llm_decision = {
        'intent': intent['intent'],
        'tool_type': intent['tool_type'],
        'tool_name': None,
        'arguments': intent['arguments'],
        'confidence': intent['confidence'],
        'requires_tool': intent['tool_type'] != 'chat',
        'reasoning_summary': f"Intención detectada: {intent['intent']}",
        'missing_arguments': []
    }
    
    # Obtener nombre de tool específica si aplica
    if intent['tool_type'] == 'weather':
        llm_decision['tool_name'] = 'weather.get_current_weather'
    elif intent['tool_type'] == 'mcp':
        tool_name = intent['arguments'].get('tool_name', 'say_hello')
        llm_decision['tool_name'] = f'mcp.{tool_name}'
    elif intent['tool_type'] == 'chat':
        llm_decision['tool_name'] = 'chat.respond'
    
    # Registrar decisión del LLM
    logger.log_llm_decision(
        session_id=session_id,
        turn_id=turn_id,
        user_message=user_message,
        llm_decision=llm_decision,
        latency_ms=latency_ms
    )
    
    new_state = dict(state)
    new_state['llm_decision'] = llm_decision
    new_state['intent'] = intent['intent']
    new_state['tool_to_use'] = intent['tool_type']
    new_state['tool_args'] = intent['arguments']
    
    return new_state


def validate_decision_node(state: OrquestadorState) -> OrquestadorState:
    """Nodo: Valida determinísticamente la decisión del LLM"""
    llm_decision = state.get('llm_decision', {})
    session_id = state.get('session_id', 'unknown')
    turn_id = state.get('turn_id', 0)
    
    # Validar contra el registry
    tool_name = llm_decision.get('tool_name')
    arguments = llm_decision.get('arguments', {})
    
    # Medir tiempo de validación
    start_time = time.time()
    
    if tool_name:
        validation_result = tool_registry.validate_call(tool_name, arguments)
    else:
        # No requiere herramienta, validación vacía
        validation_result = {
            'valid': True,
            'tool_name': 'chat',
            'arguments': arguments,
            'errors': [],
            'missing_arguments': []
        }
    
    latency_ms = (time.time() - start_time) * 1000
    
    # Convertir ValidationResult a dict
    validation_dict = {
        'valid': validation_result.valid,
        'tool_name': validation_result.tool_name,
        'arguments': validation_result.arguments,
        'errors': validation_result.errors,
        'missing_arguments': validation_result.missing_arguments
    }
    
    # Registrar validación
    logger.log_tool_validation(
        session_id=session_id,
        turn_id=turn_id,
        tool_name=tool_name or 'chat',
        valid=validation_result.valid,
        errors=validation_result.errors,
        latency_ms=latency_ms
    )
    
    new_state = dict(state)
    new_state['validation_result'] = validation_dict
    
    # Añadir errores al estado si hay
    if validation_result.errors:
        new_state['errors'] = state.get('errors', []) + validation_result.errors
    
    return new_state


def route_request_node(state: OrquestadorState) -> OrquestadorState:
    """Nodo: Decide si ejecutar herramienta o responder con chat"""
    validation_result = state.get('validation_result', {})
    
    new_state = dict(state)
    
    if validation_result.get('valid', False):
        # Validación exitosa, route según tool_name
        tool_name = validation_result.get('tool_name', '')
        
        if tool_name.startswith('weather.'):
            new_state['next_node'] = 'execute_tool'
        elif tool_name.startswith('mcp.'):
            new_state['next_node'] = 'execute_tool'
        elif tool_name.startswith('chat.'):
            new_state['next_node'] = 'generic_chat'
        else:
            new_state['next_node'] = 'generic_chat'
    else:
        # Validación fallida, usar chat genérico con explicación
        new_state['next_node'] = 'generic_chat'
    
    return new_state


def execute_tool_node(state: OrquestadorState) -> OrquestadorState:
    """Nodo: Ejecuta la herramienta real seleccionada"""
    orquestador = AgentOrquestador()
    session_id = state.get('session_id', 'unknown')
    turn_id = state.get('turn_id', 0)
    
    validation_result = state.get('validation_result', {})
    tool_name = validation_result.get('tool_name', '')
    arguments = validation_result.get('arguments', {})
    
    # Medir tiempo de ejecución
    start_time = time.time()
    
    # Ejecutar herramienta
    if tool_name == 'weather.get_current_weather':
        location = arguments.get('location')
        result = execute_weather_agent(location) if location else None
        
        if result and result.get('success'):
            analysis = result.get('analysis')
            if analysis:
                response_text = f"🌞 Clima en {analysis['location']}:\n"
                response_text += f"   - Temperatura: {analysis['temperature_celsius']}°C\n"
                response_text += f"   - Condición: {analysis['condition']}\n"
                
                # Añadir recomendaciones
                recommendations = result.get('recommendations', [])
                if recommendations:
                    response_text += "\n💡 Recomendaciones:\n"
                    for rec in recommendations:
                        response_text += f"   - {rec}\n"
            else:
                response_text = "❌ No se pudieron obtener datos climáticos."
        else:
            response_text = f"❌ Error obteniendo clima: {result.get('error', 'Desconocido')}" if result else "❌ Error desconocido"
        
        new_state = dict(state)
        new_state['tool_result'] = result
        new_state['final_response'] = response_text
        
        # Registrar ejecución
        latency_ms = (time.time() - start_time) * 1000
        logger.log_tool_execution(
            session_id=session_id,
            turn_id=turn_id,
            tool_name=tool_name,
            success=result.get('success', False) if result else False,
            latency_ms=latency_ms
        )
        
    elif tool_name.startswith('mcp.'):
        # Extraer tool_name real (quitando prefijo mcp.)
        mcp_tool = tool_name.split('.', 1)[1]
        result = execute_mcp_tool(mcp_tool, arguments)
        
        if result.get('success'):
            response_text = result.get('response', 'Operación completada')
        else:
            response_text = f"❌ Error en herramienta MCP: {result.get('error', 'Desconocido')}"
        
        new_state = dict(state)
        new_state['tool_result'] = result
        new_state['final_response'] = response_text
        
    else:
        # Tool desconocida, fallback a chat
        new_state = dict(state)
        new_state['final_response'] = "No tengo acceso a esa herramienta específica."
    
    return new_state


def generic_chat_node(state: OrquestadorState) -> OrquestadorState:
    """Nodo: Genera respuesta conversacional sin tool"""
    validation_result = state.get('validation_result', {})
    errors = state.get('errors', [])
    
    # Si hay errores de validación, informar al usuario
    if errors:
        response_text = "⚠️ No pude ejecutar la solicitud:\n"
        for error in errors[-3:]:  # Mostrar últimos 3 errores
            response_text += f"   - {error}\n"
        response_text += "\n¿Puedes reformular tu pregunta?"
    else:
        # Respuesta genérica
        response_text = "Entiendo tu consulta. En esta versión del sistema, puedo:\n"
        response_text += "   - Consultar el clima de una ciudad\n"
        response_text += "   - Saludarte en diferentes idiomas\n"
        response_text += "   - Conversar sobre temas generales\n\n"
        response_text += "¿En qué puedo ayudarte?"
    
    new_state = dict(state)
    new_state['final_response'] = response_text
    
    return new_state


def format_response_node(state: OrquestadorState) -> OrquestadorState:
    """Nodo: Formatea la respuesta final"""
    # El formato ya está hecho en los nodos anteriores
    # Este nodo solo asegura que el formato sea consistente
    new_state = dict(state)
    
    # Actualizar campo 'response' para compatibilidad
    new_state['response'] = state.get('final_response')
    
    return new_state


def persist_memory_node(state: OrquestadorState) -> OrquestadorState:
    """Nodo: Persiste información en memoria"""
    # En una implementación real, esto guardaría en FAISS
    # Por ahora, solo registramos el turno
    new_state = dict(state)
    
    # Añadir a conversation_history si hay user_message y final_response
    user_message = state.get('user_message', state.get('user_input', ''))
    final_response = state.get('final_response', '')
    
    if user_message and final_response:
        history = state.get('conversation_history', [])
        history.append({'role': 'user', 'content': user_message})
        history.append({'role': 'assistant', 'content': final_response})
        new_state['conversation_history'] = history[-10:]  # Mantener últimos 10
    
    return new_state


# ==================== COMPILACIÓN DEL GRAFO ====================

def build_orquestador_graph() -> CompiledStateGraph:
    """Construye y compila el grafo LangGraph del orquestador"""
    builder = StateGraph(OrquestadorState)
    
    # Añadir nodos
    builder.add_node("load_context", load_context_node)
    builder.add_node("retrieve_memory", retrieve_memory_node)
    builder.add_node("analyze_intent", analyze_intent_node)
    builder.add_node("validate_decision", validate_decision_node)
    builder.add_node("route_request", route_request_node)
    builder.add_node("execute_tool", execute_tool_node)
    builder.add_node("generic_chat", generic_chat_node)
    builder.add_node("format_response", format_response_node)
    builder.add_node("persist_memory", persist_memory_node)
    
    # Definir flujo
    builder.add_edge(START, "load_context")
    builder.add_edge("load_context", "retrieve_memory")
    builder.add_edge("retrieve_memory", "analyze_intent")
    builder.add_edge("analyze_intent", "validate_decision")
    builder.add_edge("validate_decision", "route_request")
    
    # Condicional en route_request
    builder.add_conditional_edges(
        "route_request",
        lambda state: state.get('next_node', 'generic_chat'),
        {
            "execute_tool": "execute_tool",
            "generic_chat": "generic_chat"
        }
    )
    
    builder.add_edge("execute_tool", "format_response")
    builder.add_edge("generic_chat", "format_response")
    builder.add_edge("format_response", "persist_memory")
    builder.add_edge("persist_memory", END)
    
    return builder.compile()


# Compilar el grafo
graph = build_orquestador_graph()


def run_orquestador(user_input: str, history: Optional[Sequence[dict[str, str]]] = None) -> dict:
    """
    Ejecuta el agente orquestador
    
    Args:
        user_input: Mensaje del usuario
        history: Historial de conversación
    
    Returns:
        Resultado del agente
    """
    if history is None:
        history = []
    
    initial_state = {
        "session_id": "",
        "turn_id": 0,
        "user_message": user_input,
        "conversation_history": list(history),
        "retrieved_memories": [],
        "available_tools": [],
        "llm_decision": None,
        "validation_result": None,
        "tool_result": None,
        "final_response": None,
        "errors": []
    }
    
    try:
        result = graph.invoke(initial_state)
        
        return {
            "success": True,
            "user_input": user_input,
            "session_id": result.get('session_id'),
            "turn_id": result.get('turn_id'),
            "intent": result.get('intent'),
            "tool_used": result.get('tool_to_use'),
            "tool_args": result.get('tool_args'),
            "response": result.get('final_response'),
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "user_input": user_input,
            "response": f"❌ Error procesando solicitud: {str(e)}"
        }


# Exportar para uso directo
__all__ = ['run_orquestador', 'AgentOrquestador', 'graph', 'tool_registry']
