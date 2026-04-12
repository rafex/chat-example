"""
Agente Orquestador con LangGraph
Decide qué herramienta usar según la intención del usuario usando LLM
"""

from typing import TypedDict, Annotated, Sequence, Optional, Literal, Any
from langgraph.graph import StateGraph, END
from datetime import datetime
import re
import json
import sys
import os

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
]

for path in paths_to_add:
    if path not in sys.path:
        sys.path.insert(0, path)

try:
    from src.schemas.orquestador import OrquestadorState, IntentAnalysis, ToolExecutionResult, ToolType
    from src.services.weather_agent_wrapper import execute_weather_agent, extract_location_from_text
    from src.services.mcp_wrapper import execute_mcp_tool, list_mcp_tools
except ImportError as e:
    # Importar schemas directamente
    from orquestador import OrquestadorState, IntentAnalysis, ToolExecutionResult, ToolType
    from weather_agent_wrapper import execute_weather_agent, extract_location_from_text
    from mcp_wrapper import execute_mcp_tool, list_mcp_tools


class AgentOrquestador:
    """Clase principal del agente orquestador con LLM"""
    
    def __init__(self):
        # Añadir paths del agente meteorológico para DeepSeek
        agent_weather_root = os.path.join(project_root, 'poc', 'agent-weather')
        agent_weather_src = os.path.join(agent_weather_root, 'src')
        
        # Para imports como 'from src.config import Config', 
        # necesitamos que el directorio padre de 'src' esté en sys.path
        # (es decir, 'poc/agent-weather')
        paths_to_add = [
            agent_weather_root,  # Permite 'from src.config import Config'
            agent_weather_src,   # Por si acaso se usa 'from config import Config'
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
    
    def analyze_intent_with_llm(self, user_input: str, history: Sequence[dict[str, str]]) -> IntentAnalysis:
        """
        Analiza la intención del usuario usando LLM
        
        Args:
            user_input: Mensaje del usuario
            history: Historial de conversación
        
        Returns:
            Análisis de intención
        """
        if not self.llm_available:
            return self.analyze_intent_by_rules(user_input, history)
        
        # Construir mensajes para el LLM
        messages = []
        
        # Añadir historial
        for msg in history[-5:]:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
        
        # Añadir instrucciones del sistema
        available_tools = "\n".join([f"- {tool}" for tool in self.mcp_tool_names])
        
        # Obtener detalles de herramientas MCP con parámetros
        mcp_tools_details = []
        for tool in self.mcp_tools:
            tool_name = tool.get('name', '')
            tool_params = tool.get('parameters', {})
            params_str = ""
            if tool_params:
                if isinstance(tool_params, dict):
                    params_str = ", ".join([f"{k}={k}" for k in tool_params.keys()])
                elif isinstance(tool_params, list):
                    params_str = ", ".join(tool_params)
            mcp_tools_details.append(f"- {tool_name}({params_str})")
        
        system_prompt = f"""Eres un asistente inteligente que analiza la intención del usuario y decide qué herramienta usar.

⚠️  REGLA DE ORO: Usa SOLO las herramientas listadas aquí. NUNCA inventes nombres de herramientas.

HERRAMIENTAS DISPONIBLES:
- Agente Meteorológico: Para consultas de clima (ej: "¿Qué tiempo hace en Madrid?")
{available_tools}
- Chat Genérico: Para conversación general

DETALLES DE HERRAMIENTAS MCP:
{chr(10).join(mcp_tools_details) if mcp_tools_details else "No hay herramientas MCP disponibles"}

INSTRUCCIONES:
1. Identifica la intención del usuario
2. Determina qué herramienta usar: "weather", "mcp", o "chat"
3. Si es "mcp", usa SOLO los nombres de herramientas listados arriba
4. Extrae argumentos relevantes (como ubicación para clima, nombre para saludos, etc.)
5. Devuelve un JSON con la siguiente estructura:
{{
  "intent": "string describing the intent",
  "tool_type": "weather" | "mcp" | "chat",
  "tool_name": "nombre de la herramienta MCP (solo si tool_type es mcp)",
  "arguments": {{"key": "value"}},
  "confidence": 0.0-1.0
}}

EJEMPLOS:
Usuario: "¿Cómo está el clima en Madrid?"
{{
  "intent": "weather_query",
  "tool_type": "weather",
  "arguments": {{"location": "Madrid"}},
  "confidence": 0.95
}}

Usuario: "say_hello(name=Juan, lang=es)"
{{
  "intent": "mcp_say_hello",
  "tool_type": "mcp",
  "tool_name": "say_hello",
  "arguments": {{"name": "Juan", "lang": "es"}},
  "confidence": 0.98
}}

Usuario: "Hola, ¿cómo estás?"
{{
  "intent": "general_chat",
  "tool_type": "chat",
  "arguments": {{}},
  "confidence": 0.8
}}

IMPORTANTE: Si el usuario pide múltiples idiomas y no hay herramienta multilingüe,
responde usando la herramienta existente apropiadamente. NO inventes herramientas.

Devuelve solo el JSON, sin texto adicional:
"""
        
        messages.insert(0, {"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_input})
        
        try:
            response = self.llm.chat(messages)
            
            # Parsear respuesta JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                
                # Asegurar que tool_name esté en arguments para herramientas MCP
                arguments = result.get("arguments", {})
                if result.get("tool_type") == "mcp" and "tool_name" not in arguments:
                    # Extraer tool_name del intent o usar el nombre de la herramienta
                    intent_name = result.get("intent", "")
                    if intent_name.startswith("mcp_"):
                        arguments["tool_name"] = intent_name[4:]
                
                return {
                    "intent": result.get("intent", "general_chat"),
                    "confidence": result.get("confidence", 0.7),
                    "tool_type": result.get("tool_type", "chat"),
                    "arguments": arguments
                }
        except Exception as e:
            print(f"⚠️  Error con LLM, usando análisis por reglas: {e}")
        
        return self.analyze_intent_by_rules(user_input, history)
    
    def analyze_intent_by_rules(self, user_input: str, history: Sequence[dict[str, str]]) -> IntentAnalysis:
        """
        Analiza la intención del usuario usando reglas (fallback del LLM)
        
        Args:
            user_input: Mensaje del usuario
            history: Historial de conversación
        
        Returns:
            Análisis de intención
        """
        # Palabras clave para clima
        weather_keywords = [
            'clima', 'weather', 'temperatura', ' temperatura', 'lluvia', 'rain',
            'sol', 'sun', 'viento', 'wind', 'humedad', 'humidity', 'nieve', 'snow',
            'nubes', 'clouds', 'amanecer', 'atardecer', 'predicción', 'forecast',
            'tiempo', 'hace', 'hoy', 'mañana'
        ]
        
        # Palabras clave para MCP
        mcp_keywords = [
            'hola', 'hello', 'saludar', 'greet', 'idioma', 'language',
            'herramienta', 'tool', 'mcp', 'servicio', 'service',
            'saluda', 'decir', 'hablar'
        ]
        
        user_input_lower = user_input.lower()
        
        # Verificar si es consulta de clima
        weather_match = any(keyword in user_input_lower for keyword in weather_keywords)
        
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


# Funciones para LangGraph

def analyze_intent_node(state: OrquestadorState) -> OrquestadorState:
    """Nodo: Analizar intención del usuario"""
    orquestador = AgentOrquestador()
    intent = orquestador.analyze_intent(state['user_input'], state.get('history', []))
    
    return {
        **state,
        'intent': intent['intent'],
        'tool_to_use': intent['tool_type'],
        'tool_args': intent['arguments']
    }


def execute_tool_node(state: OrquestadorState) -> OrquestadorState:
    """Nodo: Ejecutar herramienta seleccionada"""
    orquestador = AgentOrquestador()
    
    intent = {
        'intent': state.get('intent', ''),
        'tool_type': state['tool_to_use'],
        'arguments': state.get('tool_args', {})
    }
    
    result = orquestador.execute_tool(intent)
    
    return {
        **state,
        'response': result['response'],
        'error': None if result['success'] else result['response']
    }


# Construir grafo LangGraph
builder = StateGraph(OrquestadorState)

builder.add_node("analyze_intent", analyze_intent_node)
builder.add_node("execute_tool", execute_tool_node)

builder.set_entry_point("analyze_intent")
builder.add_edge("analyze_intent", "execute_tool")
builder.add_edge("execute_tool", END)

graph = builder.compile()


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
        "user_input": user_input,
        "intent": None,
        "tool_to_use": None,
        "tool_args": None,
        "response": None,
        "history": history,
        "error": None
    }
    
    try:
        result = graph.invoke(initial_state)
        
        return {
            "success": True,
            "user_input": user_input,
            "intent": result.get('intent'),
            "tool_used": result.get('tool_to_use'),
            "tool_args": result.get('tool_args'),
            "response": result.get('response'),
            "error": result.get('error')
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "user_input": user_input,
            "response": f"❌ Error procesando solicitud: {str(e)}"
        }


# Exportar para uso directo
__all__ = ['run_orquestador', 'AgentOrquestador', 'graph']
