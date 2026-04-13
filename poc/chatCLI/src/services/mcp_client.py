"""
Cliente para comunicarse con MCP servers
Implementa el protocolo JSON-RPC de MCP
"""
import json
import subprocess
import sys
from typing import Any, Dict, List, Optional
from pathlib import Path


class MCPClient:
    """Cliente para MCP que inicia un servidor subprocess y comunica vía JSON-RPC"""

    def __init__(self, server_path: str):
        """
        Inicia el servidor MCP como subprocess

        Args:
            server_path: Ruta al script del servidor MCP (ej: /path/to/server.py)
        """
        self.server_path = server_path
        self.process = None
        self.request_id_counter = 0
        self._start_server()

    def _start_server(self):
        """Inicia el servidor MCP como subprocess"""
        if not Path(self.server_path).exists():
            raise FileNotFoundError(f"MCP server no encontrado: {self.server_path}")

        try:
            self.process = subprocess.Popen(
                [sys.executable, self.server_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False,  # Usar bytes
                bufsize=0,  # Sin buffer
            )
            print(f"✅ MCP Server iniciado: {self.server_path}")
        except Exception as e:
            raise RuntimeError(f"Error iniciando MCP server: {e}")

    def _send_request(self, method: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Envía un request JSON-RPC al servidor MCP"""
        if not self.process or self.process.poll() is not None:
            raise RuntimeError("MCP Server no está activo")

        self.request_id_counter += 1
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "id": self.request_id_counter,
        }
        if params:
            request["params"] = params

        # Serializar a JSON y enviar con header Content-Length
        body = json.dumps(request, ensure_ascii=False).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8")

        try:
            self.process.stdin.write(header)
            self.process.stdin.write(body)
            self.process.stdin.flush()
        except Exception as e:
            raise RuntimeError(f"Error escribiendo al MCP server: {e}")

        # Leer response
        return self._read_response()

    def _read_response(self) -> Dict[str, Any]:
        """Lee un response JSON-RPC del servidor"""
        if not self.process:
            raise RuntimeError("MCP Server no está activo")

        try:
            # Leer header Content-Length
            content_length = None
            while True:
                header_line = self.process.stdout.readline()
                if not header_line:
                    raise RuntimeError("MCP Server cerró la conexión")

                decoded = header_line.decode("utf-8").strip()
                if decoded == "":
                    break

                if decoded.lower().startswith("content-length:"):
                    content_length = int(decoded.split(":", 1)[1].strip())

            if content_length is None:
                raise RuntimeError("No Content-Length header en respuesta MCP")

            # Leer body
            body = self.process.stdout.read(content_length)
            if not body:
                raise RuntimeError("MCP Server no envió respuesta")

            return json.loads(body.decode("utf-8"))
        except Exception as e:
            raise RuntimeError(f"Error leyendo respuesta MCP: {e}")

    def initialize(self) -> Dict[str, Any]:
        """Inicializa la conexión MCP"""
        return self._send_request("initialize")

    def list_tools(self) -> List[Dict[str, Any]]:
        """Lista herramientas disponibles en el servidor MCP"""
        response = self._send_request("tools/list")
        return response.get("result", {}).get("tools", [])

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta una herramienta MCP"""
        response = self._send_request(
            "tools/call",
            {
                "name": tool_name,
                "arguments": arguments,
            },
        )

        result = response.get("result", {})
        # Extraer el contenido de texto si es disponible
        if "content" in result and result["content"]:
            content_list = result["content"]
            if isinstance(content_list, list) and content_list:
                first_content = content_list[0]
                if isinstance(first_content, dict) and "text" in first_content:
                    text = first_content["text"]
                    try:
                        return json.loads(text)
                    except json.JSONDecodeError:
                        return {"text": text}

        return result

    def close(self):
        """Cierra el servidor MCP"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception as e:
                print(f"⚠️ Error cerrando MCP server: {e}")
                self.process.kill()

    def __del__(self):
        self.close()
