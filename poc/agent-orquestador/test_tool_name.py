import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))

paths = [
    os.path.join(current_dir, 'src', 'agents'),
    os.path.join(current_dir, 'src', 'services'),
    os.path.join(project_root, 'lib'),
    os.path.join(project_root, 'poc', 'agent-weather', 'src'),
    os.path.join(project_root, 'poc', 'agent-weather', 'src', 'services'),
    os.path.join(project_root, 'poc', 'agent-weather', 'src', 'schemas'),
    os.path.join(project_root, 'poc', 'agent-weather'),
]

for p in paths:
    sys.path.insert(0, p)

from orquestador_agent import AgentOrquestador

orquestador = AgentOrquestador()

print('Probando análisis de intención...')
user_input = 'usa el mcp para saludarme en varios idiomas'
intent = orquestador.analyze_intent(user_input, [])
print(f'Intent: {intent}')
print()

# Verificar qué herramienta MCP se va a ejecutar
tool_name = intent['arguments'].get('tool_name', 'say_hello')
print(f'Tool name to execute: {tool_name}')
print()

# Ejecutar manualmente
from mcp_wrapper import execute_mcp_tool
result = execute_mcp_tool(tool_name, {})
print(f'Response from wrapper: {result["response"]}')
