import sys
import os

# Calcular rutas desde agent-orquestador
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))

paths_to_add = [
    os.path.join(current_dir, 'src'),
    project_root,
    os.path.join(project_root, 'poc', 'agent-weather', 'src'),
    os.path.join(project_root, 'poc', 'agent-weather', 'src', 'services'),
    os.path.join(project_root, 'poc', 'agent-weather', 'src', 'schemas'),
    os.path.join(project_root, 'poc', 'agent-weather'),
]

for path in paths_to_add:
    if path not in sys.path:
        sys.path.insert(0, path)

agents_dir = os.path.join(current_dir, 'src', 'agents')
sys.path.insert(0, agents_dir)

import orquestador_agent

print('=== PRUEBA AGENTE ORQUESTADOR CON LLM ===')
print()

orquestador = orquestador_agent.AgentOrquestador()
print(f'LLM disponible: {orquestador.llm_available}')
print()

# Probar ejecución completa
test_cases = [
    'usa el mcp para saludarme en varios idiomas',
    'hola, ¿cómo estás?',
    'say_hello(name=Carlos, lang=es)',
]

for i, user_input in enumerate(test_cases, 1):
    print(f'Test {i}: "{user_input}"')
    result = orquestador_agent.run_orquestador(user_input)
    print(f'  Success: {result["success"]}')
    print(f'  Intent: {result.get("intent")}')
    print(f'  Tool used: {result.get("tool_used")}')
    print(f'  Response: {result.get("response")[:200]}...')
    print()
