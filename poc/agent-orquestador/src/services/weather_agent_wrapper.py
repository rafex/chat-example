"""
Wrapper para el agente meteorológico
"""

import sys
import os
import subprocess
import json
from typing import Optional

# Calcular rutas
current_file = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file)
agent_orquestador_src = os.path.dirname(current_dir)
agent_orquestador_root = os.path.dirname(agent_orquestador_src)
project_root = os.path.dirname(os.path.dirname(agent_orquestador_root))

agent_weather_root = os.path.join(project_root, 'poc', 'agent-weather')
agent_weather_src = os.path.join(agent_weather_root, 'src')

WEATHER_AGENT_AVAILABLE = False

# Verificar que el script del agente meteorológico existe
weather_script = os.path.join(agent_weather_src, 'agents', 'weather_agent.py')
if os.path.exists(weather_script):
    WEATHER_AGENT_AVAILABLE = True


def execute_weather_agent(location: str) -> dict:
    """
    Ejecuta el agente meteorológico usando subprocess
    """
    if not WEATHER_AGENT_AVAILABLE:
        return {
            "success": False,
            "error": "Agente meteorológico no disponible",
            "location": location,
            "recommendations": []
        }
    
    try:
        # Crear script temporal para ejecutar el agente
        script = f'''
import sys
import os
import json

# Añadir paths necesarios
agent_weather_src = r"{agent_weather_src}"
sys.path.insert(0, agent_weather_src)
sys.path.insert(0, os.path.join(agent_weather_src, "agents"))
sys.path.insert(0, os.path.join(agent_weather_src, "services"))
sys.path.insert(0, os.path.join(agent_weather_src, "schemas"))
sys.path.insert(0, r"{agent_weather_root}")
sys.path.insert(0, r"{project_root}")

# Suprimir warnings
import warnings
warnings.filterwarnings("ignore")

# Importar y ejecutar
from weather_agent import run_weather_agent
result = run_weather_agent(r"{location}")
print(json.dumps(result, default=str))
'''
        
        # Ejecutar el script
        result = subprocess.run(
            [sys.executable, '-c', script],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            # Filtrar solo la línea JSON del stdout
            stdout_lines = result.stdout.strip().split('\n')
            json_line = None
            for line in stdout_lines:
                if line.strip().startswith('{'):
                    json_line = line.strip()
                    break
            
            if json_line:
                return json.loads(json_line)
            else:
                return {
                    "success": False,
                    "error": f"No se encontró JSON en la salida: {result.stdout[:200]}",
                    "location": location,
                    "recommendations": []
                }
        else:
            return {
                "success": False,
                "error": result.stderr or "Error desconocido",
                "location": location,
                "recommendations": []
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "location": location,
            "recommendations": []
        }


def extract_location_from_text(text: str) -> Optional[str]:
    """
    Extrae ubicación de texto usando patrones comunes
    """
    import re
    
    # Ciudades españolas comunes
    cities = [
        'Madrid', 'Barcelona', 'Valencia', 'Sevilla', 'Bilbao',
        'Zaragoza', 'Palma', 'Murcia', 'Granada', 'Alicante',
        'Córdoba', 'Valladolid', 'Vigo', 'Gijón', 'L Hospitalet',
        'Vitoria', 'La Coruña', 'Elche', 'Terrassa'
    ]
    
    # Patrones para extraer ubicación
    patterns = [
        r'en\s+(\w+(?:\s+\w+)*?)\s*(?:\?|\.|$|,)',
        r'en\s+(\w+(?:\s+\w+)*?)\s*$',
    ]
    
    # Buscar ciudad específica
    for city in cities:
        if city.lower() in text.lower():
            return city
    
    # Buscar patrones gramaticales
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            location = match.group(1).strip()
            if location.title() in cities:
                return location.title()
    
    return None
