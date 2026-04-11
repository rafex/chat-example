#!/usr/bin/env python3
"""
Router MCP para unificar servicios en un solo punto de entrada.
"""

from __future__ import annotations

import json
import sys
import os
from typing import Any, Callable, Dict


class MCPRouter:
    """Router que maneja múltiples servicios MCP."""
    
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.resources: Dict[str, Callable] = {}
        self.prompts: Dict[str, Callable] = {}
        
        # Registrar herramientas
        self.register_tool("say_hello", self.handle_say_hello)
        self.register_tool("get_hello_languages", self.handle_get_hello_languages)
        
        # Registrar recursos (ejemplo)
        self.register_resource("hello://service-overview", self.handle_service_overview)
        
        # Registrar prompts (ejemplo)
        self.register_prompt("greet-user", self.handle_greet_user)
    
    def register_tool(self, name: str, handler: Callable):
        """Registrar una herramienta."""
        self.tools[name] = handler
    
    def register_resource(self, uri: str, handler: Callable):
        """Registrar un recurso."""
        self.resources[uri] = handler
    
    def register_prompt(self, name: str, handler: Callable):
        """Registrar un prompt."""
        self.prompts[name] = handler
    
    def handle_request(self, request: dict[str, Any]) -> dict[str, Any] | None:
        """Manejar una solicitud MCP."""
        method = request.get("method")
        request_id = request.get("id")
        
        if method == "notifications/initialized":
            return None
        
        if method == "initialize":
            return self.success(
                request_id,
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
                    "serverInfo": {"name": "mcp-router", "version": "0.1.0"},
                },
            )
        
        if method == "tools/list":
            return self.success(
                request_id,
                {
                    "tools": [
                        {
                            "name": name,
                            "description": "Herramienta MCP",
                            "inputSchema": {"type": "object", "properties": {}},
                        }
                        for name in self.tools.keys()
                    ]
                },
            )
        
        if method == "tools/call":
            params = request.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name not in self.tools:
                return self.error(request_id, -32602, f"Herramienta no soportada: {tool_name}")
            
            try:
                result = self.tools[tool_name](arguments)
                return self.success(
                    request_id,
                    {
                        "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}],
                        "structuredContent": result,
                        "isError": False,
                    },
                )
            except Exception as e:
                return self.error(request_id, -32000, f"Error ejecutando herramienta: {str(e)}")
        
        if method == "resources/list":
            return self.success(
                request_id,
                {
                    "resources": [
                        {"uri": uri, "name": uri, "description": "Recurso MCP"}
                        for uri in self.resources.keys()
                    ]
                },
            )
        
        if method == "resources/read":
            params = request.get("params", {})
            resource_uri = params.get("uri")
            
            if resource_uri not in self.resources:
                return self.error(request_id, -32602, f"Recurso no soportado: {resource_uri}")
            
            try:
                result = self.resources[resource_uri](params)
                return self.success(request_id, result)
            except Exception as e:
                return self.error(request_id, -32000, f"Error leyendo recurso: {str(e)}")
        
        if method == "prompts/list":
            return self.success(
                request_id,
                {
                    "prompts": [
                        {"name": name, "description": "Prompt MCP"}
                        for name in self.prompts.keys()
                    ]
                },
            )
        
        if method == "prompts/get":
            params = request.get("params", {})
            prompt_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if prompt_name not in self.prompts:
                return self.error(request_id, -32602, f"Prompt no soportado: {prompt_name}")
            
            try:
                result = self.prompts[prompt_name](arguments)
                return self.success(request_id, result)
            except Exception as e:
                return self.error(request_id, -32000, f"Error obteniendo prompt: {str(e)}")
        
        return self.error(request_id, -32601, f"Método no encontrado: {method}")
    
    def success(self, request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
        """Respuesta exitosa."""
        return {"jsonrpc": "2.0", "id": request_id, "result": result}
    
    def error(self, request_id: Any, code: int, message: str) -> dict[str, Any]:
        """Respuesta con error."""
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}
    
    # Handlers para herramientas registradas
    def handle_say_hello(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Manejar herramienta say_hello."""
        # Diccionario de saludos en diferentes idiomas
        greetings = {
            "en": "Hello",
            "es": "Hola",
            "fr": "Bonjour",
            "de": "Hallo",
            "it": "Ciao",
            "pt": "Olá",
            "ru": "Privet",
            "ja": "Konnichiwa",
            "zh": "Nǐ hǎo",
            "ko": "Annyeonghaseyo",
        }
        
        name = arguments.get("name")
        lang = arguments.get("lang", "en")
        ip = arguments.get("ip", "127.0.0.1")
        
        # Normalizar idioma
        normalized_lang = lang.strip().lower() if lang else "en"
        if normalized_lang not in greetings:
            normalized_lang = "en"
        
        greeting = greetings[normalized_lang]
        
        if name:
            message = f"{greeting} {name}!"
        else:
            message = f"{greeting}!"
        
        return {
            "message": message,
            "timestamp": "00:00:00 UTC",
            "ip": ip,
            "lang": normalized_lang,
            "has_name": bool(name),
            "name": name
        }
    
    def handle_get_hello_languages(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Manejar herramienta get_hello_languages."""
        return {
            "count": 10,
            "languages": ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "zh", "ko"],
        }
    
    # Handlers para recursos
    def handle_service_overview(self, params: dict[str, Any]) -> dict[str, Any]:
        """Manejar recurso service-overview."""
        return {
            "name": "MCP Router",
            "version": "0.1.0",
            "services": ["hello"],
            "description": "Router para servicios MCP",
        }
    
    # Handlers para prompts
    def handle_greet_user(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Manejar prompt greet-user."""
        name = arguments.get("name", "Usuario")
        lang = arguments.get("lang", "es")
        
        # Usar el mismo handler de say_hello
        payload = self.handle_say_hello({"name": name, "lang": lang})
        
        return {
            "messages": [
                {"role": "system", "content": "Eres un asistente amable que saluda al usuario."},
                {"role": "user", "content": f"Saluda a {name} en {lang}"},
                {"role": "assistant", "content": payload["message"]},
            ]
        }


def main() -> None:
    """Punto de entrada del router MCP."""
    router = MCPRouter()
    
    while True:
        request = read_message()
        if request is None:
            return
        response = router.handle_request(request)
        if response is not None:
            write_message(response)


def read_message() -> dict[str, Any] | None:
    """Leer mensaje JSON-RPC de stdin."""
    content_length: int | None = None
    
    while True:
        header_line = sys.stdin.buffer.readline()
        if not header_line:
            return None
        
        decoded = header_line.decode("utf-8").strip()
        if decoded == "":
            break
        
        if decoded.lower().startswith("content-length:"):
            content_length = int(decoded.split(":", 1)[1].strip())
    
    if content_length is None:
        return None
    
    body = sys.stdin.buffer.read(content_length)
    if not body:
        return None
    return json.loads(body.decode("utf-8"))


def write_message(payload: dict[str, Any]) -> None:
    """Escribir mensaje JSON-RPC a stdout."""
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8")
    sys.stdout.buffer.write(header)
    sys.stdout.buffer.write(body)
    sys.stdout.buffer.flush()


if __name__ == "__main__":
    main()
