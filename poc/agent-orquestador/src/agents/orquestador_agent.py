"""
Agente Orquestador con LangGraph
Decide qué herramienta usar según la intención del usuario
"""

from typing import TypedDict, Annotated, Sequence, Optional, Literal, Any
from langgraph.graph import StateGraph, END
from datetime import datetime
import re

# Importar wrappers
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
agent_orquestador_src = os.path.dirname(current_dir)  # poc/agent-orquestador/src
project_root = os.path.dirname(os.path.dirname(agent_orquestador_src))  # agentes-con-LangGraph

# Añadir paths necesarios
sys.path.insert(0, agent_orquestador_src)
sys.path.insert(0, project_root)

# Añadir path de agent-weather para los wrappers
agent_weather_src = os.path.join(project_root, 'poc', 'agent-weather', 'src')
sys.path.insert(0, agent_weather_src)
sys.path.insert(0, os.path.join(agent_weather_src, 'agents'))

# Añadir path de lib para MCP
lib_path = os.path.join(project_root, 'lib')
sys.path.insert(0, lib_path)

try:
    from src.schemas.orquestador import OrquestadorState, IntentAnalysis, ToolExecutionResult, ToolType
    from src.services.weather_agent_wrapper import execute_weather_agent, extract_location_from_text
    from src.services.mcp_wrapper import execute_mcp_tool, list_mcp_tools
except ImportError as e:
    print(f"⚠️  Error importando módulos: {e}")
    # Importar schemas directamente
    sys.path.insert(0, os.path.join(agent_orquestador_src, 'schemas'))
    sys.path.insert(0, os.path.join(agent_orquestador_src, 'services'))
    from orquestador import OrquestadorState, IntentAnalysis, ToolExecutionResult, ToolType
    from weather_agent_wrapper import execute_weather_agent, extract_location_from_text
    from mcp_wrapper import execute_mcp_tool, list_mcp_tools


class AgentOrquestador:
    """Clase principal del agente orquestador"""
    
    def __init__(self):
        self.weather_keywords = [
            'clima', 'weather', 'temperatura', ' temperatura', 'lluvia', 'rain',
            'sol', 'sun', 'viento', 'wind', 'humedad', 'humidity', 'nieve', 'snow',
            'nubes', 'clouds', 'amanecer', 'atardecer', 'predicción', 'forecast'
        ]
        
        self.mcp_keywords = [
            'hola', 'hello', 'saludar', 'greet', 'idioma', 'language',
            'herramienta', 'tool', 'mcp', 'servicio', 'service'
        ]
        
        # Listar herramientas MCP disponibles
        try:
            self.mcp_tools = list_mcp_tools()
            self.mcp_tool_names = [tool['name'] for tool in self.mcp_tools]
        except:
            self.mcp_tools = []
            self.mcp_tool_names = ['say_hello', 'get_hello_languages']
    
    def analyze_intent(self, user_input: str, history: Sequence[dict[str, str]]) -> IntentAnalysis:
        """
        Analiza la intención del usuario
        
        Args:
            user_input: Mensaje del usuario
            history: Historial de conversación
        
        Returns:
            Análisis de intención
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
                        # Extraer ubicación de "vive en X"
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
    
    def execute_tool(self, intent: IntentAnalysis) -> ToolExecutionResult:
        """
        Ejecuta la herramienta determinada por el análisis de intención
        
        Args:
            intent: Análisis de intención
        
        Returns:
            Resultado de la ejecución
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
            # Chat genérico (por ahora, respuesta simple)
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
