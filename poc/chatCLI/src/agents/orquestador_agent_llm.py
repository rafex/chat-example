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

# Importar servicios usando rutas absolutas para evitar colisión de namespaces
# con agent-weather (ambos tienen un paquete llamado 'services')
def _import_from_file(module_name: str, file_path: str):
    """Carga un módulo desde su ruta absoluta, sin depender de sys.path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None:
        raise ImportError(f"No se pudo crear spec para {file_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_services_dir = os.path.join(_chatcli_src, "services")

try:
    _mcp_mod = _import_from_file("chatcli_mcp_client", os.path.join(_services_dir, "mcp_client.py"))
    MCPClient = _mcp_mod.MCPClient
except Exception as e:
    print(f"⚠️ MCPClient no disponible: {e}")
    MCPClient = None

try:
    _agent_client_mod = _import_from_file("chatcli_agent_client", os.path.join(_services_dir, "agent_client.py"))
    _weather_fn = _agent_client_mod.call_weather_agent
    _WEATHER_AVAILABLE = True
except Exception as e:
    print(f"⚠️ AgentClient no disponible: {e}")
    _weather_fn = None
    _WEATHER_AVAILABLE = False


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
        """Registra agentes internos accesibles via AgentClient (subprocess)."""
        if _WEATHER_AVAILABLE:
            self.available_tools["agent/get_current_weather"] = {
                "name": "get_current_weather",
                "description": (
                    "Consulta el clima actual de una ciudad o país usando el agente meteorológico. "
                    "Úsala SIEMPRE que el usuario pregunte por el tiempo, temperatura, lluvia, "
                    "clima, condiciones meteorológicas o planee un viaje a algún lugar."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "Ciudad o país en español o inglés (ej: 'Atenas', 'Grecia', 'Madrid', 'Athens,GR')"
                        }
                    },
                    "required": ["location"],
                },
            }
            print("✅ Agente de clima registrado")

    def get_tools_description(self) -> str:
        """Genera descripción de herramientas disponibles para el LLM"""
        description = "Herramientas disponibles:\n"
        for tool_id, tool_info in self.available_tools.items():
            name = tool_info.get("name", tool_id)
            desc = tool_info.get("description", "Sin descripción")
            description += f"- {name}: {desc}\n"
        return description

    def _call_llm(self, prompt: str, system_msg: str = "") -> str:
        """Llama a DeepSeek LLM usando ruta absoluta para evitar conflictos de namespace."""
        try:
            llm_mod = _import_from_file(
                "chatcli_deepseek_service",
                os.path.join(_services_dir, "deepseek_service.py"),
            )
            service = llm_mod.LLMProviderService()
            messages = []
            if system_msg:
                messages.append({"role": "system", "content": system_msg})
            messages.append({"role": "user", "content": prompt})
            return service.chat(messages)
        except Exception as e:
            print(f"⚠️ Error llamando a LLM: {e}")
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

            system_msg = (
                "Eres el módulo de selección de herramientas de un asistente conversacional. "
                "Tu ÚNICA tarea es analizar la solicitud y decidir qué herramientas invocar. "
                "TIENES ACCESO REAL a todas las herramientas listadas: puedes y DEBES usarlas. "
                "NUNCA digas que no puedes acceder a datos en tiempo real; si la herramienta existe, ÚSALA. "
                "Responde EXCLUSIVAMENTE con un objeto JSON válido, sin texto adicional."
            )

            analysis_prompt = f"""Herramientas disponibles (TIENES ACCESO REAL A TODAS):
{tools_desc}

Solicitud del usuario: "{user_input}"

INSTRUCCIONES OBLIGATORIAS:
1. Si el usuario menciona clima, tiempo, temperatura, lluvia, viaje a algún lugar → USA "get_current_weather" con la ubicación en inglés.
2. Si el usuario pide saludo → USA "say_hello" con el código de idioma (es, en, fr, pt, zh, ru, ar, hi, bn, ur).
3. Si el usuario pregunta por idiomas soportados → USA "get_hello_languages".
4. Puedes usar MÚLTIPLES herramientas si la solicitud lo requiere.
5. El campo "tools" JAMÁS debe estar vacío si existe una herramienta relevante.

Ejemplos de ubicaciones: "nueva zelanda" → "New Zealand", "grecia" → "Greece", "japón" → "Japan".

Responde SOLO con este JSON (sin markdown, sin explicaciones):
{{
    "intention": "descripción de lo que el usuario pide",
    "tools": [
        {{"name": "nombre_herramienta", "parameters": {{"param": "valor"}}}}
    ],
    "reasoning": "por qué usas esas herramientas"
}}"""

            analysis_result = self._call_llm(analysis_prompt, system_msg=system_msg)

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
                final_system = (
                    "Eres un asistente conversacional amable. "
                    "Tienes acceso a datos REALES obtenidos por herramientas. "
                    "USA SIEMPRE los datos proporcionados y NUNCA digas que no tienes acceso a información en tiempo real. "
                    "Si hay datos de clima, preséntales de forma clara e incluye recomendaciones prácticas."
                )
                final_prompt = f"""El usuario dijo: "{user_input}"

Datos obtenidos por las herramientas (son REALES y actuales):
{json.dumps(tool_results, indent=2, ensure_ascii=False)}

Genera una respuesta amable, clara y útil basada EXCLUSIVAMENTE en estos datos reales."""

                final_response = self._call_llm(final_prompt, system_msg=final_system)
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

                # Si es agente externo (subprocess via AgentClient)
                elif tool_id.startswith("agent/"):
                    if tool_name == "get_current_weather" and _weather_fn:
                        location = parameters.get("location")
                        if not location:
                            raise ValueError("Parámetro 'location' requerido")
                        return _weather_fn(location)
                    else:
                        raise RuntimeError(f"Agente externo '{tool_name}' no implementado")

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
