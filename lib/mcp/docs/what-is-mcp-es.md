# Qué Es MCP

## Definición

MCP significa Model Context Protocol.

Es un protocolo diseñado para que un modelo o una aplicación cliente pueda conectarse a capacidades externas de forma estandarizada. Esas capacidades pueden incluir:

- herramientas
- recursos
- prompts
- operaciones especializadas

En términos prácticos, MCP define una forma común para que un cliente descubra qué ofrece un servidor y luego lo invoque con mensajes estructurados.

## Qué problema resuelve

Sin MCP, cada integración suele inventar su propio contrato:

- nombres de operaciones
- formato de entrada
- formato de salida
- secuencia de inicialización
- forma de anunciar capacidades

Eso genera integraciones acopladas y poco reutilizables.

MCP propone una base común para:

- iniciar una sesión
- negociar capacidades
- listar herramientas
- ejecutar herramientas
- intercambiar datos estructurados

## Idea mental simple

Una forma útil de pensarlo es esta:

- REST describe recursos y operaciones HTTP
- MCP describe capacidades y herramientas para clientes compatibles con IA

No cumplen exactamente la misma función, pero ambos buscan interoperabilidad.

## Piezas principales

### Cliente MCP

Es la aplicación que consume el servidor MCP.

Ejemplos:

- una app de escritorio
- una extensión
- un IDE
- un runtime que integra herramientas para un modelo

### Servidor MCP

Es el proceso o servicio que expone capacidades.

Puede ofrecer:

- `tools/list`
- `tools/call`
- recursos
- prompts

### Protocolo de mensajes

MCP suele usar JSON-RPC 2.0 como base estructural.

Eso introduce campos como:

- `jsonrpc`
- `id`
- `method`
- `params`

Y respuestas con:

- `result`
- `error`

## Flujo mínimo típico

Un flujo básico suele ser:

1. el cliente abre la conexión con el servidor
2. envía `initialize`
3. el servidor responde con versión y capacidades
4. el cliente solicita `tools/list`
5. el servidor anuncia herramientas disponibles
6. el cliente llama `tools/call`
7. el servidor devuelve un resultado estructurado

## Por qué importa en este repositorio

Este proyecto compara REST y MCP sobre el mismo caso funcional para estudiar:

- qué cambia en el transporte
- qué cambia en el descubrimiento de capacidades
- qué se mantiene igual en la lógica del dominio
