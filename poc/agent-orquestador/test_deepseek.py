import sys
import os

# Calcular rutas desde agent-orquestador
current_dir = os.path.dirname(os.path.abspath(__file__))  # poc/agent-orquestador
project_root = os.path.dirname(os.path.dirname(current_dir))  # agentes-con-LangGraph

print(f'current_dir: {current_dir}')
print(f'project_root: {project_root}')

paths_to_add = [
    os.path.join(current_dir, 'src'),  # poc/agent-orquestador/src
    project_root,
    os.path.join(project_root, 'poc', 'agent-weather', 'src'),
    os.path.join(project_root, 'poc', 'agent-weather', 'src', 'services'),
    os.path.join(project_root, 'poc', 'agent-weather', 'src', 'schemas'),
    os.path.join(project_root, 'poc', 'agent-weather'),
]

for path in paths_to_add:
    if path not in sys.path:
        sys.path.insert(0, path)
        print(f'Añadido: {path}')

print(f'\nIntentando importar deepseek_service...')
try:
    from deepseek_service import DeepSeekService
    print('✅ Importación exitosa')
    llm = DeepSeekService()
    print(f'✅ LLM creado: {type(llm)}')
    response = llm.generate('Hola')
    print(f'Respuesta: {response[:100]}...')
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
