import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))

paths = [
    os.path.join(current_dir, 'src', 'services'),
    os.path.join(project_root, 'lib'),
]

for p in paths:
    sys.path.insert(0, p)

from mcp_wrapper import execute_mcp_tool

print('Probando ejecución directa del wrapper MCP...')
result = execute_mcp_tool('get_hello_languages', {})
print(f'Success: {result["success"]}')
print(f'Response: {result["response"]}')
print(f'Raw: {result["raw_response"]}')
