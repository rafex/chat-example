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

try:
    from mcp_wrapper import execute_mcp_tool, list_mcp_tools
    print('✅ Importación exitosa')
    
    # Probar get_hello_languages
    result = execute_mcp_tool('get_hello_languages', {})
    print(f'Resultado: {result}')
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
