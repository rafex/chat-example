from __future__ import annotations

import json
import os
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SERVER_INFO = {"name": "hello-python-mcp", "version": "0.1.0"}
PROTOCOL_VERSION = "2024-11-05"
HELLO_API_BASE_URL = os.getenv("HELLO_API_BASE_URL", "http://127.0.0.1:8080")


def main() -> None:
    while True:
        request = read_message()
        if request is None:
            return
        response = handle_request(request)
        if response is not None:
            write_message(response)


def read_message() -> dict[str, Any] | None:
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
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8")
    sys.stdout.buffer.write(header)
    sys.stdout.buffer.write(body)
    sys.stdout.buffer.flush()


def handle_request(request: dict[str, Any]) -> dict[str, Any] | None:
    method = request.get("method")
    request_id = request.get("id")

    if method == "notifications/initialized":
        return None

    if method == "initialize":
        return success(
            request_id,
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
                "serverInfo": SERVER_INFO,
            },
        )

    if method == "tools/list":
        return success(
            request_id,
            {
                "tools": [
                    {
                        "name": "say_hello",
                        "description": "Devuelve un saludo opcionalmente personalizado y localizado en uno de los 10 idiomas soportados.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "Nombre opcional a saludar."},
                                "lang": {"type": "string", "description": "Idioma del saludo, por ejemplo en o es."},
                                "ip": {"type": "string", "description": "IP opcional a reflejar en la respuesta."},
                            },
                            "additionalProperties": False,
                        },
                    },
                    {
                        "name": "get_hello_languages",
                        "description": "Devuelve la cantidad de idiomas soportados y sus códigos.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {},
                            "additionalProperties": False,
                        },
                    },
                ]
            },
        )

    if method == "tools/call":
        params = request.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        if tool_name == "get_hello_languages":
            payload = call_hello_languages_api()
            return success(
                request_id,
                {
                    "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}],
                    "structuredContent": payload,
                    "isError": False,
                },
            )

        if tool_name != "say_hello":
            return error(request_id, -32602, f"Herramienta no soportada: {tool_name}")

        payload = call_hello_api(
            name=arguments.get("name"),
            lang=arguments.get("lang"),
            ip=arguments.get("ip") or "127.0.0.1",
        )
        return success(
            request_id,
            {
                "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}],
                "structuredContent": payload,
                "isError": False,
            },
        )

    if method == "resources/list":
        return success(request_id, call_api_json("/hello/resources"))

    if method == "resources/read":
        params = request.get("params", {})
        resource_uri = params.get("uri")
        resource_path = map_resource_uri_to_path(resource_uri)
        if resource_path is None:
            return error(request_id, -32602, f"Resource no soportado: {resource_uri}")
        return success(request_id, call_api_json(resource_path))

    if method == "prompts/list":
        return success(request_id, call_api_json("/hello/prompts"))

    if method == "prompts/get":
        params = request.get("params", {})
        prompt_name = params.get("name")
        arguments = params.get("arguments", {})
        prompt_path = build_prompt_path(prompt_name, arguments)
        if prompt_path is None:
            return error(request_id, -32602, f"Prompt no soportado: {prompt_name}")
        return success(request_id, call_api_json(prompt_path))

    return error(request_id, -32601, f"Método no encontrado: {method}")


def success(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def call_hello_api(name: str | None, lang: str | None, ip: str) -> dict[str, Any]:
    params: dict[str, str] = {}
    if name:
        params["name"] = name
    if lang:
        params["lang"] = lang

    query = urlencode(params)
    url = f"{HELLO_API_BASE_URL}/hello"
    if query:
        url = f"{url}?{query}"

    request = Request(url, method="GET", headers={"X-Forwarded-For": ip})
    try:
        with urlopen(request, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exception:
        detail = exception.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"REST backend responded with HTTP {exception.code}: {detail}") from exception
    except URLError as exception:
        raise RuntimeError(f"REST backend unavailable at {HELLO_API_BASE_URL}: {exception.reason}") from exception


def call_hello_languages_api() -> dict[str, Any]:
    request = Request(f"{HELLO_API_BASE_URL}/hello/languages", method="GET")
    try:
        with urlopen(request, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exception:
        detail = exception.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"REST backend responded with HTTP {exception.code}: {detail}") from exception
    except URLError as exception:
        raise RuntimeError(f"REST backend unavailable at {HELLO_API_BASE_URL}: {exception.reason}") from exception


def call_api_json(path: str) -> dict[str, Any]:
    request = Request(f"{HELLO_API_BASE_URL}{path}", method="GET")
    try:
        with urlopen(request, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exception:
        detail = exception.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"REST backend responded with HTTP {exception.code}: {detail}") from exception
    except URLError as exception:
        raise RuntimeError(f"REST backend unavailable at {HELLO_API_BASE_URL}: {exception.reason}") from exception


def map_resource_uri_to_path(resource_uri: str | None) -> str | None:
    if resource_uri == "hello://service-overview":
        return "/hello/resources/service-overview"
    if resource_uri == "hello://language-reference":
        return "/hello/resources/language-reference"
    return None


def build_prompt_path(prompt_name: str | None, arguments: dict[str, Any]) -> str | None:
    if prompt_name == "greet-user":
        query = urlencode(
            {
                key: value
                for key, value in {
                    "name": arguments.get("name"),
                    "lang": arguments.get("lang"),
                }.items()
                if value
            }
        )
        return f"/hello/prompts/greet-user?{query}" if query else "/hello/prompts/greet-user"
    if prompt_name == "language-report":
        query = urlencode({"name": arguments.get("name")}) if arguments.get("name") else ""
        return f"/hello/prompts/language-report?{query}" if query else "/hello/prompts/language-report"
    return None


if __name__ == "__main__":
    main()
