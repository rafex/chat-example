"""
Wrapper para el MCP Router
"""

import sys
import os
import json

# Calcular rutas absolutas
current_dir = os.path.dirname(os.path.abspath(__file__))
agent_orquestador_src = os.path.dirname(current_dir)  # poc/agent-orquestador/src
agent_orquestador_root = os.path.dirname(agent_orquestador_src)  # poc/agent-orquestador
project_root = os.path.dirname(os.path.dirname(agent_orquestador_root))  # agentes-con-LangGraph

# El MCP Router está en: agentes-con-LangGraph/lib/mcp
lib_path = os.path.join(project_root, 'lib')
sys.path.insert(0, lib_path)

try:
    from mcp.router import MCPRouter
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print(f"⚠️  MCP Router no disponible en {lib_path}")


def execute_mcp_tool(tool_name: str, arguments: dict) -> dict:
    """
    Ejecuta una herramienta MCP con validación
    
    Args:
        tool_name: Nombre de la herramienta
        arguments: Argumentos para la herramienta
    
    Returns:
        Resultado de la ejecución
    """
    if not MCP_AVAILABLE:
        return {
            "success": False,
            "error": "MCP Router no disponible",
            "tool_used": tool_name,
            "response": ""
        }
    
    # Validar que la herramienta existe
    available_tools = list_mcp_tools()
    available_tool_names = [tool.get('name', '') for tool in available_tools]
    
    if tool_name not in available_tool_names:
        return {
            "success": False,
            "error": f"La herramienta '{tool_name}' no existe",
            "available_tools": available_tool_names,
            "tool_used": tool_name,
            "response": f"❌ La herramienta '{tool_name}' no está disponible. Herramientas disponibles: {', '.join(available_tool_names)}"
        }
    
    try:
        router = MCPRouter()
        
        # Construir solicitud MCP
        request = {
            "method": "tools/call",
            "id": 1,
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        response = router.handle_request(request)
        
        if response and 'result' in response:
            content = response['result']['content'][0]['text']
            result_data = json.loads(content)
            
            # Extraer mensaje de la respuesta
            response_text = ""
            if isinstance(result_data, dict):
                # Para herramientas como say_hello
                if 'message' in result_data:
                    response_text = result_data['message']
                # Para herramientas como get_hello_languages
                elif 'count' in result_data and 'languages' in result_data:
                    languages = result_data['languages']
                    count = result_data['count']
                    response_text = f"Language tool available! Supports {count} languages: {', '.join(languages)}"
                else:
                    response_text = str(result_data)
            else:
                response_text = str(result_data)
            
            return {
                "success": True,
                "tool_used": tool_name,
                "tool_args": arguments,
                "response": response_text,
                "raw_response": result_data
            }
        else:
            return {
                "success": False,
                "error": "Respuesta inválida del MCP",
                "tool_used": tool_name,
                "response": f"❌ Error al ejecutar '{tool_name}': Respuesta inválida del servidor MCP"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "tool_used": tool_name,
            "response": f"❌ Error ejecutando '{tool_name}': {str(e)}"
        }


def list_mcp_tools() -> list[dict]:
    """
    Lista las herramientas disponibles en MCP
    
    Returns:
        Lista de herramientas disponibles
    """
    if not MCP_AVAILABLE:
        return []
    
    try:
        router = MCPRouter()
        
        request = {
            "method": "tools/list",
            "id": 1
        }
        
        response = router.handle_request(request)
        
        if response and 'result' in response:
            return response['result'].get('tools', [])
        else:
            return []
    except Exception as e:
        print(f"Error listando herramientas MCP: {e}")
        return []
