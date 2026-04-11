# MCP Server And Transport Types

## Core idea

When people talk about the "type of MCP server", they are often really talking about the transport the server uses to communicate with the client.

The server logic may stay the same, while the channel changes.

## 1. `stdio`

This is the most common transport for minimal examples and local integrations.

Characteristics:

- local child process
- input through `stdin`
- output through `stdout`
- `Content-Length` framing

This is the type currently used in this repository.

## 2. HTTP

An MCP server can be exposed over HTTP.

Characteristics:

- runs as a network service
- fits web infrastructure better
- easier to inspect with HTTP tooling

It is usually useful when you need:

- remote access
- network observability
- centralized deployment

## 3. SSE

SSE stands for Server-Sent Events.

It can be useful when the server needs to push events to the client over HTTP infrastructure.

Characteristics:

- suitable for more interactive sessions
- built on familiar web infrastructure
- can coexist with traditional HTTP requests

## 4. WebSocket

Some implementations or adapters may use WebSocket for persistent bidirectional communication.

Characteristics:

- long-lived connection
- continuous message exchange
- useful for sessions with frequent traffic

## 5. Bridges or adapters

It is also common to adapt one transport into another.

Examples:

- a local `stdio` process behind an HTTP entry point
- an MCP server exposed through a gateway
- an adapter that converts REST into MCP or MCP into REST

## What should not be confused

It is useful to separate these ideas:

- MCP: protocol
- JSON-RPC: common structural message format
- `stdio`, HTTP, SSE, WebSocket: transports or channels

## Relationship with Bruno and Postman

Bruno and Postman work very well with HTTP.

That is why:

- the repository REST APIs are described with OpenAPI
- `stdio` MCP servers are not consumed directly like a REST API

If you want to use classic HTTP tooling with a `stdio` MCP server, you typically need an HTTP bridge.
