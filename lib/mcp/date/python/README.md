# MCP Date Python

Wrapper MCP sobre el backend REST `api-date` Python.

## Idea principal

Este MCP no calcula la hora por sí mismo. Su trabajo es:

1. recibir peticiones MCP por `stdio`
2. traducirlas a llamadas HTTP al backend REST
3. añadir internamente los headers de autenticación
4. devolver el resultado al cliente MCP

Así, el agente de IA no necesita saber nada sobre:

- `Authorization: Bearer <token>`
- `X-Date-Client: <client-id>`

## Qué expone

### Tools

- `get_current_time`
- `list_supported_locations`

### Resources

- `date://auth-reference`
- `date://location-reference`

### Prompts

- `single-location-time`
- `compare-locations`

## Variables de entorno

- `DATE_API_BASE_URL`
- `DATE_API_TOKEN`
- `DATE_API_CLIENT_ID`

Valores por defecto:

- `DATE_API_BASE_URL=http://127.0.0.1:8090`
- `DATE_API_TOKEN=dev-date-token`
- `DATE_API_CLIENT_ID=mcp-date-client`

## Cómo ejecutarlo

Primero levanta el backend REST:

```bash
just run-python-api-date
```

Luego, en otra terminal:

```bash
just run-python-mcp-date
```

## Cómo probarlo

La forma más simple es usar el script de prueba:

```bash
./scripts/test-mcp-date-python.sh
```

Ese script:

1. levanta el backend REST Python con un puerto aislado
2. arranca el servidor MCP Python
3. envía `initialize`
4. lista tools, resources y prompts
5. ejecuta `list_supported_locations`
6. ejecuta `get_current_time`
