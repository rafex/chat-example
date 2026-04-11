import sys
import os

# Añadir paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))

paths_to_add = [
    os.path.join(current_dir, 'src'),
    project_root,
    os.path.join(project_root, 'poc', 'agent-weather', 'src'),
    os.path.join(project_root, 'poc', 'agent-weather', 'src', 'services'),
    os.path.join(project_root, 'poc', 'agent-weather', 'src', 'schemas'),
    os.path.join(project_root, 'poc', 'agent-weather'),
    os.path.join(project_root, 'lib'),
]

for path in paths_to_add:
    if path not in sys.path:
        sys.path.insert(0, path)

from src.services.mcp_wrapper import execute_mcp_tool, list_mcp_tools

print('=== PRUEBA WRAPPER MCP ===')
print()

# Listar herramientas
tools = list_mcp_tools()
print(f'Herramientas disponibles: {[t["name"] for t in tools]}')
print()

# Probar get_hello_languages
print('Probando get_hello_languages...')
result = execute_mcp_tool('get_hello_languages', {})
print(f'Success: {result["success"]}')
print(f'Response: {result["response"]}')
print(f'Raw: {result.get("raw_response")}')
print()

# Probar say_hello
print('Probando say_hello...')
result = execute_mcp_tool('say_hello', {'name': 'Juan', 'lang': 'es'})
print(f'Success: {result["success"]}')
print(f'Response: {result["response"]}')
