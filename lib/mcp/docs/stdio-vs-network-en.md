# MCP Over `stdio` Vs Network Transport

## MCP Over `stdio`

In this model, the client starts the MCP server as a local process.

Communication happens through:

- `stdin` for input
- `stdout` for output
- optional `stderr` for logs

Messages commonly use this framing:

```text
Content-Length: <n>

<json>
```

The body is usually JSON-RPC.

## Advantages of `stdio`

- simple for examples and local tooling
- no ports or HTTP server required
- reduces network exposure
- works well when the client controls the child process

## Drawbacks of `stdio`

- not convenient for HTTP tools such as Postman or Bruno
- lifecycle depends on the local process
- traffic inspection is less direct
- scaling simultaneous connections may require extra work

## When to use `stdio`

- local integrations
- educational examples
- tools launched by a local client
- scenarios where the client starts the server

## MCP Over The Network

In this model, the MCP server lives as a network-accessible service.

Depending on the implementation, it may use:

- HTTP
- SSE
- WebSocket
- other compatible transports

## Advantages of network transport

- integrates better with web infrastructure
- easier to observe
- can be consumed by remote clients
- fits centralized deployments better

## Drawbacks of network transport

- requires more infrastructure
- introduces authentication, ports, and deployment concerns
- usually more complex for a minimal example

## Key difference

The main difference is not the protocol idea itself, but the channel.

In both cases, the client and server can still exchange:

- `initialize`
- `tools/list`
- `tools/call`

What changes is how the messages travel.
