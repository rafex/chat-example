# Tipos De Servidor Y Transporte MCP

## Idea central

Cuando se habla del "tipo de servidor MCP", muchas veces en realidad se está hablando del transporte que usa el servidor para comunicarse con el cliente.

La lógica del servidor puede ser la misma, pero el canal cambia.

## 1. `stdio`

Es el transporte más común para ejemplos mínimos e integraciones locales.

Características:

- proceso hijo local
- entrada por `stdin`
- salida por `stdout`
- framing con `Content-Length`

Es el tipo que usamos actualmente en este repositorio.

## 2. HTTP

Un servidor MCP puede exponerse mediante HTTP.

Características:

- corre como servicio de red
- encaja mejor con infraestructura web
- es más fácil de inspeccionar con herramientas HTTP

Suele ser útil cuando se necesita:

- acceso remoto
- observabilidad de red
- despliegue centralizado

## 3. SSE

SSE significa Server-Sent Events.

Puede ser útil cuando el servidor necesita empujar eventos al cliente sobre infraestructura HTTP.

Características:

- adecuado para sesiones más interactivas
- se apoya en una base web conocida
- puede convivir con peticiones HTTP tradicionales

## 4. WebSocket

Algunas implementaciones o adaptadores pueden usar WebSocket para comunicación bidireccional persistente.

Características:

- conexión duradera
- intercambio continuo de mensajes
- útil para sesiones con tráfico frecuente

## 5. Bridges o adaptadores

También es común adaptar un transporte a otro.

Ejemplos:

- un proceso local `stdio` detrás de una puerta HTTP
- un servidor MCP expuesto mediante un gateway
- un adaptador que convierte REST en MCP o MCP en REST

## Qué no debe confundirse

Conviene separar estas ideas:

- MCP: protocolo
- JSON-RPC: formato estructural frecuente del mensaje
- `stdio`, HTTP, SSE, WebSocket: transportes o canales

## Relación con Bruno y Postman

Bruno y Postman trabajan muy bien con HTTP.

Por eso:

- los APIs REST del repositorio se describen con OpenAPI
- los MCP `stdio` no se consumen directamente igual que una API REST

Si se quiere usar tooling HTTP clásico con un MCP `stdio`, normalmente hace falta un bridge HTTP.
