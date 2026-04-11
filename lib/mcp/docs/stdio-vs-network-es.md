# MCP Sobre `stdio` Vs Transporte De Red

## MCP Sobre `stdio`

En este modelo, el cliente lanza el servidor MCP como un proceso local.

La comunicación ocurre usando:

- `stdin` para entrada
- `stdout` para salida
- `stderr` opcional para logs

Los mensajes suelen usar este framing:

```text
Content-Length: <n>

<json>
```

El cuerpo normalmente es JSON-RPC.

## Ventajas de `stdio`

- es simple para ejemplos y tooling local
- no requiere puertos ni servidor HTTP
- reduce exposición de red
- encaja bien cuando el cliente controla el proceso hijo

## Desventajas de `stdio`

- no es cómodo para herramientas HTTP como Postman o Bruno
- el ciclo de vida depende del proceso local
- observar el tráfico puede ser menos directo
- escalar conexiones simultáneas puede requerir más trabajo

## Cuándo usar `stdio`

- integraciones locales
- ejemplos educativos
- herramientas ejecutadas por un cliente local
- escenarios donde el cliente arranca el servidor

## MCP Sobre Red

En este modelo, el servidor MCP vive como un servicio accesible por red.

Según la implementación, puede usar:

- HTTP
- SSE
- WebSocket
- otros transportes compatibles

## Ventajas del transporte de red

- se integra mejor con infraestructura web
- es más fácil de observar
- puede ser consumido por clientes remotos
- se adapta mejor a despliegues centralizados

## Desventajas del transporte de red

- requiere más infraestructura
- introduce autenticación, puertos y despliegue
- para un ejemplo mínimo suele ser más complejo

## Diferencia clave

La diferencia principal no está en la idea del protocolo, sino en el canal.

En ambos casos el cliente y el servidor pueden seguir intercambiando:

- `initialize`
- `tools/list`
- `tools/call`

Lo que cambia es cómo viajan los mensajes.
