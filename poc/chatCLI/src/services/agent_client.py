"""
AgentClient: invoca agentes externos como subprocesos independientes.

Mismo patrón que MCPClient pero para agentes Python con su propio entorno.
El agente corre en un proceso hijo aislado → sin colisión de namespaces ni
conflictos de imports relativos.

Flujo:
  orchestrator → AgentClient.call_agent("weather", {location: "Atenas"})
              → subprocess python -c "...run_weather_agent('Atenas')..."
              → stdout JSON
              → dict resultado
"""
import json
import os
import subprocess
import sys
from typing import Any, Dict

_current_dir = os.path.dirname(os.path.abspath(__file__))
_chatcli_src = os.path.dirname(_current_dir)
_chatcli_dir = os.path.dirname(_chatcli_src)
_poc_dir = os.path.dirname(_chatcli_dir)


# Rutas conocidas de agentes disponibles
_AGENTS_PATHS = {
    "weather": os.path.join(_poc_dir, "agent-weather"),
}


def _build_weather_script(agent_root: str, location: str) -> str:
    """Genera el script Python que se ejecutará en el subprocess."""
    # Escapar comillas simples en location para evitar problemas en el script
    safe_location = location.replace("'", "\\'")
    return (
        f"import sys, json\n"
        f"sys.path.insert(0, {repr(agent_root)})\n"
        f"from src.agents.weather_agent import run_weather_agent\n"
        f"result = run_weather_agent({repr(location)})\n"
        f"print(json.dumps(result, ensure_ascii=False, default=str))\n"
    )


def call_weather_agent(location: str) -> Dict[str, Any]:
    """
    Invoca run_weather_agent de agent-weather en un subprocess aislado.

    Args:
        location: Ciudad o país (ej: "Atenas", "Greece", "Madrid,ES")

    Returns:
        Dict con los datos del clima o {"success": False, "error": "..."}
    """
    agent_root = _AGENTS_PATHS.get("weather")
    if not agent_root or not os.path.isdir(agent_root):
        return {
            "success": False,
            "error": f"Directorio de agent-weather no encontrado: {agent_root}",
        }

    script = _build_weather_script(agent_root, location)

    try:
        proc = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=agent_root,
        )

        if proc.returncode != 0:
            stderr = proc.stderr.strip()
            return {
                "success": False,
                "error": f"Error en agent-weather: {stderr[-500:] if len(stderr) > 500 else stderr}",
            }

        stdout = proc.stdout.strip()
        if not stdout:
            return {"success": False, "error": "agent-weather no produjo salida"}

        # Tomar solo la última línea (puede haber prints de inicialización antes)
        last_line = stdout.splitlines()[-1]
        return json.loads(last_line)

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Timeout: agent-weather tardó más de 30s"}
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"Respuesta no es JSON válido: {e}. Output: {stdout[:200]}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
