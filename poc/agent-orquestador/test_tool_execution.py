import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))

paths = [
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

print('Probando ejecución de get_hello_languages...')
result = execute_mcp_tool('get_hello_languages', {})
print(f'Success: {result["success"]}')
print(f'Tool used: {result["tool_used"]}')
print(f'Response: {result["response"]}')
print(f'Raw response: {result["raw_response"]}')
print()

print('Probando ejecución de say_hello...')
result = execute_mcp_tool('say_hello', {'name': 'Juan', 'lang': 'es'})
print(f'Success: {result["success"]}')
print(f'Tool used: {result["tool_used"]}')
print(f'Response: {result["response"]}')
print(f'Raw response: {result["raw_response"]}')
