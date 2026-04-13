"""
Orquestador dinámico con LLM usando DeepSeek
Analiza la intención del usuario y ejecuta herramientas automáticamente
"""
import json
import os
import sys
import importlib.util
from typing import Any, Dict, List, Optional, Sequence
from datetime import datetime

# Configurar paths
_current_file = os.path.abspath(__file__)
_agents_dir = os.path.dirname(_current_file)
_chatcli_src = os.path.dirname(_agents_dir)
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(_chatcli_src)))

if _chatcli_src not in sys.path:
    sys.path.insert(0, _chatcli_src)

# Importar servicios
try:
    from services.mcp_client import MCPClient
except ImportError as e:
    print(f"⚠️ MCPClient no disponible: {e}")
    MCPClient = None

# Nota: El weather agent no está habilitado en chatCLI debido a conflictos de path
# El agente de clima se puede invocar directamente desde agent-weather/
# Para chatCLI, nos enfocamos en MCP tools que se registran dinámicamente


# Nota: get_weather_agent() no está implementado en chatCLI debido a conflictos de path
# El weather agent se ejecuta desde agent-weather/ como un módulo independiente


class LLMOrchestrator:
    """Orquestador dinámico que usa LLM para decisiones"""

    def __init__(self, mcp_server_path: Optional[str] = None):
        """
        Inicializa el orquestador

        Args:
            mcp_server_path: Ruta al servidor MCP (ej: /path/to/mcp/hello/python/server.py)
        """
        self.mcp_client = None
        self.mcp_tools = []
        self.available_tools = {}

        # Inicializar MCP si está disponible
        if mcp_server_path and MCPClient:
            try:
                self.mcp_client = MCPClient(mcp_server_path)
                self.mcp_client.initialize()
                self.mcp_tools = self.mcp_client.list_tools()
                print(f"✅ MCP client inicializado con {len(self.mcp_tools)} herramientas")

                # Crear mapeo de herramientas MCP
                for tool in self.mcp_tools:
                    tool_name = tool.get('name', 'UNNAMED')
                    tool_id = f"mcp/{tool_name}"
                    self.available_tools[tool_id] = tool
            except Exception as e:
                print(f"⚠️ Error inicializando MCP: {e}")
                self.mcp_client = None

        # Registrar herramientas internas
        self._register_internal_tools()

    def _register_internal_tools(self):
        """Registra herramientas internas

        Nota: En chatCLI usamos principalmente herramientas MCP.
        Las herramientas internas (como weather) se pueden agregar aquí si es necesario.
        """
        pass  # Las herramientas MCP se registran automáticamente en __init__

    def get_tools_description(self) -> str:
        """Genera descripción de herramientas disponibles para el LLM"""
        description = "Herramientas disponibles:\n"
        for tool_id, tool_info in self.available_tools.items():
            name = tool_info.get("name", tool_id)
            desc = tool_info.get("description", "Sin descripción")
            description += f"- {name}: {desc}\n"
        return description

    def _call_llm(self, prompt: str) -> str:
        """Llama a DeepSeek LLM"""
        try:
            # Importar servicio de LLM local
            import sys
            import os
            services_dir = os.path.join(os.path.dirname(__file__), '..', 'services')
            if services_dir not in sys.path:
                sys.path.insert(0, services_dir)

            from deepseek_service import LLMProviderService

            service = LLMProviderService()
            # Usar el método chat de LLMProviderService
            response = service.chat([{"role": "user", "content": prompt}])
            return response
        except Exception as e:
            print(f"⚠️ Error llamando a LLM: {e}")
            import traceback
            traceback.print_exc()
            return ""

    def analyze_and_execute(
        self, user_input: str, conversation_history: Optional[Sequence[dict]] = None
    ) -> Dict[str, Any]:
        """
        Analiza el input del usuario y ejecuta herramientas automáticamente

        Args:
            user_input: Input del usuario
            conversation_history: Historial de conversación

        Returns:
            Dict con resultado de ejecución
        """
        if conversation_history is None:
            conversation_history = []

        try:
            # Paso 1: Analizar intención con LLM
            tools_desc = self.get_tools_description()
            analysis_prompt = f"""Eres un asistente inteligente que analiza solicitudes de usuarios y las mapea a herramientas disponibles.

IMPORTANTE: Siempre debes usar las herramientas disponibles cuando sea relevante.

Herramientas disponibles:
{tools_desc}

Input del usuario: "{user_input}"

Analiza y responde SIEMPRE en JSON VÁLIDO con esta estructura exacta:
{{
    "intention": "descripción clara de lo que el usuario pide",
    "tools": [
        {{
            "name": "nombre exacto de la herramienta a usar",
            "parameters": {{"param": "valor"}}
        }}
    ],
    "reasoning": "por qué usaste esas herramientas"
}}

REGLAS:
- Si el usuario pide un saludo: usa "say_hello" con el parámetro lang
- Si el usuario pregunta sobre clima: usa "get_current_weather" con location
- Si el usuario menciona idiomas: usa "get_hello_languages"
- SIEMPRE intenta usar una herramienta si es relevante
- El campo "tools" NUNCA debe estar vacío si hay herramientas relevantes

Responde SOLO con JSON válido, sin markdown ni explicaciones adicionales:"""

            analysis_result = self._call_llm(analysis_prompt)

            try:
                # Intentar extraer JSON del response
                json_match = analysis_result.strip()
                # Si el response comienza con markdown code fence, extraerlo
                if json_match.startswith("```"):
                    json_match = json_match.split("```")[1]
                    if json_match.startswith("json"):
                        json_match = json_match[4:]

                analysis = json.loads(json_match)
            except json.JSONDecodeError as je:
                # Si el LLM no retorna JSON válido, crear análisis fallback
                # pero igual intentar procesar la request
                print(f"⚠️ LLM no retornó JSON válido, usando fallback")

                # Intentar detectar herramientas mencionadas
                analysis = {
                    "intention": user_input[:100],
                    "tools": [],
                    "reasoning": "Fallback analysis"
                }

                # Si menciona "saludo" o "hola", usar say_hello
                if any(word in user_input.lower() for word in ["saludo", "hola", "greet", "greeting"]):
                    # Detectar idioma
                    lang = "es"  # Default
                    if "italiano" in user_input.lower() or "italian" in user_input.lower():
                        lang = "it"
                    elif "inglés" in user_input.lower() or "english" in user_input.lower():
                        lang = "en"
                    elif "francés" in user_input.lower() or "french" in user_input.lower():
                        lang = "fr"

                    analysis["tools"] = [{
                        "name": "say_hello",
                        "parameters": {"lang": lang}
                    }]
                    analysis["intention"] = f"Saludo en {lang}"

                # Si menciona "clima" o "weather", usar weather
                elif any(word in user_input.lower() for word in ["clima", "weather", "temperatura", "lluvia"]):
                    # Intentar extraer ubicación
                    try:
                        import sys
                        if _agents_dir not in sys.path:
                            sys.path.insert(0, _agents_dir)
                        from orquestador_agent import extract_location_from_text
                        location = extract_location_from_text(user_input)
                    except Exception:
                        location = None
                    if location:
                        analysis["tools"] = [{
                            "name": "get_current_weather",
                            "parameters": {"location": location}
                        }]
                        analysis["intention"] = f"Consultar clima en {location}"

            # Paso 2: Ejecutar herramientas
            tool_results = []
            tools_to_execute = analysis.get("tools", [])
            for tool_call in tools_to_execute:
                tool_name = tool_call.get("name")
                params = tool_call.get("parameters", {})

                try:
                    result = self._execute_tool(tool_name, params)
                    tool_results.append(
                        {"tool": tool_name, "success": True, "result": result}
                    )
                except Exception as e:
                    tool_results.append(
                        {"tool": tool_name, "success": False, "error": str(e)}
                    )

            # Paso 3: Generar respuesta final con LLM
            if tool_results:
                final_prompt = f"""Basándote en los siguientes resultados de herramientas,
genera una respuesta amable y útil al usuario.

Intención detectada: {analysis.get('intention')}

Resultados de herramientas:
{json.dumps(tool_results, indent=2, ensure_ascii=False)}

Input original del usuario: {user_input}

Responde de forma natural y útil:"""

                final_response = self._call_llm(final_prompt)
            else:
                final_response = (
                    "Entiendo tu solicitud: " + analysis.get("intention", "")
                )

            return {
                "success": True,
                "intention": analysis.get("intention"),
                "response": final_response,
                "tool_results": tool_results,
                "reasoning": analysis.get("reasoning"),
            }

        except Exception as e:
            return {"success": False, "error": str(e), "response": "Hubo un error procesando tu solicitud"}

    def _execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Ejecuta una herramienta específica"""
        # Normalizar parámetros de idioma
        if "lang" in parameters:
            lang_map = {
                "italian": "it", "italiano": "it",
                "spanish": "es", "español": "es",
                "english": "en", "inglés": "en",
                "french": "fr", "francés": "fr",
                "german": "de", "alemán": "de",
                "portuguese": "pt", "portugués": "pt",
                "chinese": "zh", "chino": "zh",
                "japanese": "ja", "japonés": "ja",
                "russian": "ru", "ruso": "ru",
                "korean": "ko", "coreano": "ko"
            }
            lang_value = parameters["lang"].lower().strip()
            if lang_value in lang_map:
                parameters["lang"] = lang_map[lang_value]

        # Buscar herramienta en registry
        for tool_id, tool_info in self.available_tools.items():
            if tool_info.get("name") == tool_name or tool_id.endswith(f"/{tool_name}"):
                # Si es herramienta MCP
                if tool_id.startswith("mcp/"):
                    if self.mcp_client:
                        return self.mcp_client.call_tool(tool_name, parameters)
                    else:
                        raise RuntimeError("MCP client no disponible")

        raise ValueError(f"Herramienta no encontrada: {tool_name}")

    def close(self):
        """Cierra recursos"""
        if self.mcp_client:
            self.mcp_client.close()

    def __del__(self):
        self.close()


# Instancia global del orquestador
_orchestrator = None


def get_orchestrator(mcp_server_path: Optional[str] = None) -> LLMOrchestrator:
    """Obtiene o crea la instancia del orquestador"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = LLMOrchestrator(mcp_server_path)
    return _orchestrator


def run_orchestrator_llm(
    user_input: str,
    conversation_history: Optional[Sequence[dict]] = None,
    mcp_server_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Ejecuta el orquestador con LLM"""
    orchestrator = get_orchestrator(mcp_server_path)
    return orchestrator.analyze_and_execute(user_input, conversation_history)
