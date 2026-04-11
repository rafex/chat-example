#!/usr/bin/env python3
"""
Script para probar la importación del agente meteorológico
"""

import sys
import os

# Calcular rutas
current_dir = os.path.abspath('.')
agent_orquestador_src = os.path.join(current_dir, 'src')
agent_orquestador_root = current_dir

# El proyecto raíz es agentes-con-LangGraph (el abuelo de agent-orquestador)
# agentes-con-LangGraph/poc/agent-orquestador -> agentes-con-LangGraph
project_root = os.path.dirname(os.path.dirname(agent_orquestador_root))

print(f"Rutas calculadas:")
print(f"  project_root: {project_root}")
print(f"  agent_orquestador_root: {agent_orquestador_root}")
print(f"  agent_orquestador_src: {agent_orquestador_src}")

# Paths del agente meteorológico
agent_weather_root = os.path.join(project_root, 'poc', 'agent-weather')
agent_weather_src = os.path.join(agent_weather_root, 'src')

print(f"\nPaths del agente meteorológico:")
print(f"  agent_weather_root: {agent_weather_root}")
print(f"  agent_weather_src: {agent_weather_src}")
print(f"  existe: {os.path.exists(agent_weather_src)}")

# Añadir todos los paths necesarios
sys.path.insert(0, agent_weather_src)  # src
sys.path.insert(0, os.path.join(agent_weather_src, 'agents'))  # src/agents
sys.path.insert(0, os.path.join(agent_weather_src, 'services'))  # src/services
sys.path.insert(0, os.path.join(agent_weather_src, 'schemas'))  # src/schemas
sys.path.insert(0, agent_weather_root)  # root (para .env)

print(f"\nIntentando importar el agente meteorológico...")
try:
    # Primero ver qué módulos hay disponibles
    print(f"Contenido de {agent_weather_src}:")
    print(os.listdir(agent_weather_src))

    # Intentar importar
    from agents.weather_agent import run_weather_agent
    print("✅ Agente meteorológico importado exitosamente!")
    print(f"  run_weather_agent: {run_weather_agent}")

    # Probar ejecución
    print(f"\nProbando ejecución...")
    result = run_weather_agent("Madrid")
    print(f"Resultado: {result}")

except ImportError as e:
    print(f"❌ Error de importación: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"❌ Error inesperado: {e}")
    import traceback
    traceback.print_exc()
