# MCP Date Java

Wrapper MCP sobre el backend REST `api-date` Java.

## Idea principal

Este MCP implementa un patrón muy útil para agentes:

- el backend REST mantiene autenticación y detalles operativos
- el servidor MCP ofrece una interfaz más limpia para el agente
- el wrapper traduce tools, resources y prompts a llamadas HTTP autenticadas

En otras palabras, el modelo ve capacidades de negocio y no detalles de infraestructura.

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

- `DATE_API_BASE_URL=http://127.0.0.1:8091`
- `DATE_API_TOKEN=dev-date-token`
- `DATE_API_CLIENT_ID=mcp-date-client`

## Cómo ejecutarlo

Primero levanta el backend REST:

```bash
just run-java-api-date
```

Luego, en otra terminal:

```bash
just run-java-mcp-date
```

## Cómo probarlo

```bash
./scripts/test-mcp-date-java.sh
```

Ese script compila Java, levanta el backend `api-date`, arranca el MCP y valida la conversación MCP mínima con tools, resources, prompts y llamadas reales al backend REST.
