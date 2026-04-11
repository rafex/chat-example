from __future__ import annotations

import json
import os
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


SERVER_INFO = {"name": "date-python-mcp", "version": "0.1.0"}
PROTOCOL_VERSION = "2024-11-05"
DATE_API_BASE_URL = os.getenv("DATE_API_BASE_URL", "http://127.0.0.1:8090")
DATE_API_TOKEN = os.getenv("DATE_API_TOKEN", "dev-date-token")
DATE_API_CLIENT_ID = os.getenv("DATE_API_CLIENT_ID", "mcp-date-client")


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
    sys.stdout.buffer.write(f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8"))
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
                        "name": "get_current_time",
                        "description": "Obtiene la hora actual de una ubicación soportada sin exponer auth headers al cliente.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "location": {"type": "string", "description": "Código de ubicación, por ejemplo us o mx-central."},
                                "ip": {"type": "string", "description": "IP opcional para reenviar al backend."},
                            },
                            "additionalProperties": False,
                        },
                    },
                    {
                        "name": "list_supported_locations",
                        "description": "Devuelve las ubicaciones soportadas por el servicio date.",
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
        if tool_name == "get_current_time":
            payload = call_api_json(
                "/date/time",
                {"location": arguments.get("location")},
                ip=arguments.get("ip") or "127.0.0.1",
            )
            return tool_result(request_id, payload)
        if tool_name == "list_supported_locations":
            return tool_result(request_id, call_api_json("/date/locations"))
        return error(request_id, -32602, f"Herramienta no soportada: {tool_name}")

    if method == "resources/list":
        return success(request_id, call_api_json("/date/resources"))

    if method == "resources/read":
        params = request.get("params", {})
        path = resource_path(params.get("uri"))
        if path is None:
            return error(request_id, -32602, f"Resource no soportado: {params.get('uri')}")
        return success(request_id, call_api_json(path))

    if method == "prompts/list":
        return success(request_id, call_api_json("/date/prompts"))

    if method == "prompts/get":
        params = request.get("params", {})
        path = prompt_path(params.get("name"), params.get("arguments", {}))
        if path is None:
            return error(request_id, -32602, f"Prompt no soportado: {params.get('name')}")
        return success(request_id, call_api_json(path))

    return error(request_id, -32601, f"Método no encontrado: {method}")


def tool_result(request_id: Any, payload: dict[str, Any]) -> dict[str, Any]:
    return success(
        request_id,
        {
            "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}],
            "structuredContent": payload,
            "isError": False,
        },
    )


def success(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def call_api_json(path: str, query_params: dict[str, Any] | None = None, ip: str | None = None) -> dict[str, Any]:
    query = urlencode({key: value for key, value in (query_params or {}).items() if value})
    url = f"{DATE_API_BASE_URL}{path}"
    if query:
        url = f"{url}?{query}"
    headers = {
        "Authorization": f"Bearer {DATE_API_TOKEN}",
        "X-Date-Client": DATE_API_CLIENT_ID,
    }
    if ip:
        headers["X-Forwarded-For"] = ip
    request = Request(url, method="GET", headers=headers)
    try:
        with urlopen(request, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exception:
        detail = exception.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Date REST backend responded with HTTP {exception.code}: {detail}") from exception
    except URLError as exception:
        raise RuntimeError(f"Date REST backend unavailable at {DATE_API_BASE_URL}: {exception.reason}") from exception


def resource_path(resource_uri: str | None) -> str | None:
    if resource_uri == "date://auth-reference":
        return "/date/resources/auth-reference"
    if resource_uri == "date://location-reference":
        return "/date/resources/location-reference"
    return None


def prompt_path(prompt_name: str | None, arguments: dict[str, Any]) -> str | None:
    if prompt_name == "single-location-time":
        query = urlencode({"location": arguments.get("location")}) if arguments.get("location") else ""
        return f"/date/prompts/single-location-time?{query}" if query else "/date/prompts/single-location-time"
    if prompt_name == "compare-locations":
        query = urlencode(
            {
                key: value
                for key, value in {
                    "from_location": arguments.get("from_location"),
                    "to_location": arguments.get("to_location"),
                }.items()
                if value
            }
        )
        return f"/date/prompts/compare-locations?{query}" if query else "/date/prompts/compare-locations"
    return None


if __name__ == "__main__":
    main()
