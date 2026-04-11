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

from mcp_wrapper import execute_mcp_tool

print('Probando ejecución directa con argumentos vacíos...')
result = execute_mcp_tool('get_hello_languages', {})
print(f'Response: {result["response"]}')
print()

print('Probando ejecución directa con tool_name vacío...')
result = execute_mcp_tool('', {})
print(f'Response: {result["response"]}')
print()

print('Probando ejecución directa con say_hello vacío...')
result = execute_mcp_tool('say_hello', {})
print(f'Response: {result["response"]}')
