"""
Servicio MCP (Model Context Protocol) para integrar herramientas externas.

Este módulo proporciona una interfaz para comunicarse con servidores MCP
que implementan el protocolo JSON-RPC sobre stdin/stdout.
"""

import json
import subprocess
import threading
import queue
from typing import Dict, Any, Optional, List


class MCPServer:
    """Cliente para comunicarse con un servidor MCP via stdin/stdout"""

    def __init__(self, command: List[str], name: str = "mcp-server"):
        """
        Inicializa el cliente MCP.

        Args:
            command: Comando para ejecutar el servidor MCP
            name: Nombre del servidor para logging
        """
        self.command = command
        self.name = name
        self.process: Optional[subprocess.Popen] = None
        self.request_id = 0
        self.responses: Dict[int, queue.Queue] = {}
        self.lock = threading.Lock()
        self.initialized = False
        self.available_tools: List[Dict[str, Any]] = []

    def start(self) -> bool:
        """Inicia el servidor MCP"""
        if not self.command:
            print(f"⚠️ No se puede iniciar servidor MCP {self.name}: comando no proporcionado")
            return False
        
        try:
            self.process = subprocess.Popen(
                self.command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,
            )

            # Iniciar hilo para leer respuestas
            self.reader_thread = threading.Thread(target=self._read_responses, daemon=True)
            self.reader_thread.start()

            # Inicializar servidor
            self._initialize()
            return True
        except Exception as e:
            print(f"❌ Error al iniciar servidor MCP {self.name}: {e}")
            return False

    def _initialize(self):
        """Inicializa el servidor MCP"""
        response = self.send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "chat-cli", "version": "1.0.0"}
        })

        if response and response.get("result"):
            self.initialized = True
            print(f"✅ Servidor MCP '{self.name}' inicializado")

            # Obtener lista de herramientas
            tools_response = self.send_request("tools/list", {})
            if tools_response and tools_response.get("result"):
                self.available_tools = tools_response["result"].get("tools", [])
                print(f"🔧 Herramientas disponibles: {[t['name'] for t in self.available_tools]}")

    def send_request(self, method: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Envía una solicitud JSON-RPC al servidor MCP"""
        if not self.process or self.process.poll() is not None:
            return None

        with self.lock:
            self.request_id += 1
            request_id = self.request_id

        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        }

        # Crear cola para la respuesta
        response_queue = queue.Queue()
        self.responses[request_id] = response_queue

        try:
            # Enviar solicitud
            body = json.dumps(request, ensure_ascii=False).encode("utf-8")
            header = f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8")
            if self.process and self.process.stdin:
                self.process.stdin.write(header + body)
                self.process.stdin.flush()
            else:
                return None

            # Esperar respuesta con timeout
            try:
                response = response_queue.get(timeout=5)
                return response
            except queue.Empty:
                print(f"⚠️ Timeout esperando respuesta de {self.name}")
                return None
        except Exception as e:
            print(f"❌ Error enviando solicitud a {self.name}: {e}")
            return None
        finally:
            # Limpiar cola
            self.responses.pop(request_id, None)

    def _read_responses(self):
        """Lee respuestas del servidor MCP en un hilo separado"""
        if not self.process:
            return

        while self.process and self.process.poll() is None:
            try:
                # Leer headers
                content_length = None
                while True:
                    if not self.process or not self.process.stdout:
                        break
                    header_line = self.process.stdout.readline()
                    if not header_line:
                        break

                    decoded = header_line.decode("utf-8").strip()
                    if decoded == "":
                        break

                    if decoded.lower().startswith("content-length:"):
                        content_length = int(decoded.split(":", 1)[1].strip())

                if content_length is None:
                    continue

                # Leer body
                if not self.process or not self.process.stdout:
                    continue
                body = self.process.stdout.read(content_length)
                if not body:
                    continue

                response = json.loads(body.decode("utf-8"))
                request_id = response.get("id")

                if request_id in self.responses:
                    self.responses[request_id].put(response)

            except Exception as e:
                print(f"⚠️ Error leyendo respuesta de {self.name}: {e}")
                break

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Llama a una herramienta en el servidor MCP"""
        if not self.initialized:
            print(f"⚠️ Servidor MCP {self.name} no inicializado")
            return None

        response = self.send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })

        if response and response.get("result"):
            return response["result"]
        elif response and response.get("error"):
            print(f"❌ Error llamando herramienta {tool_name}: {response['error']}")
            return None

        return None

    def stop(self):
        """Detiene el servidor MCP"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            print(f"🛑 Servidor MCP {self.name} detenido")


class HelloMCPServer(MCPServer):
    """Cliente especializado para el servidor MCP de saludos"""

    def __init__(self, mcp_path: Optional[str] = None):
        # Ruta al servidor MCP de saludos
        # Si no se proporciona, busca en la ruta relativa común
        if not mcp_path:
            # Buscar en rutas comunes
            possible_paths = [
                "/Users/rafex/repository/github/rafex/mcp-example/mcp/hello/python/server.py",
                "../mcp/hello/python/server.py",
                "mcp/hello/python/server.py",
            ]
            import os
            for path in possible_paths:
                if os.path.exists(path):
                    mcp_path = path
                    break
            
            if not mcp_path:
                print("⚠️ No se encontró el servidor MCP de saludos")
                mcp_path = ""  # Evitar error al pasar al padre
        
        super().__init__(
            command=["python3", mcp_path] if mcp_path else [],
            name="hello-mcp"
        )

    def say_hello(self, name: Optional[str] = None, lang: Optional[str] = None, ip: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Llama a la herramienta say_hello del servidor MCP"""
        arguments = {}
        if name:
            arguments["name"] = name
        if lang:
            arguments["lang"] = lang
        if ip:
            arguments["ip"] = ip

        result = self.call_tool("say_hello", arguments)
        return result

    def get_languages(self) -> Optional[Dict[str, Any]]:
        """Obtiene los idiomas soportados"""
        result = self.call_tool("get_hello_languages", {})
        return result
    
    def get_supported_languages_list(self) -> List[str]:
        """Obtiene la lista de códigos de idiomas soportados"""
        result = self.get_languages()
        if result and "structuredContent" in result:
            content = result["structuredContent"]
            if "languages" in content:
                return content["languages"]
        return ["en", "es", "fr", "zh", "hi", "ar", "bn", "pt", "ru", "ur"]  # Fallback
