# What Is MCP

## Definition

MCP stands for Model Context Protocol.

It is a protocol designed so that a model or a client application can connect to external capabilities in a standardized way. Those capabilities may include:

- tools
- resources
- prompts
- specialized operations

In practical terms, MCP defines a common way for a client to discover what a server offers and then invoke it with structured messages.

## What problem it solves

Without MCP, each integration usually invents its own contract:

- operation names
- input format
- output format
- initialization sequence
- capability announcement format

That leads to tightly coupled integrations that are hard to reuse.

MCP provides a common base for:

- starting a session
- negotiating capabilities
- listing tools
- calling tools
- exchanging structured data

## Simple mental model

A useful way to think about it is:

- REST describes resources and HTTP operations
- MCP describes capabilities and tools for AI-compatible clients

They are not exactly the same thing, but both aim for interoperability.

## Main pieces

### MCP client

This is the application that consumes the MCP server.

Examples:

- a desktop app
- an extension
- an IDE
- a runtime that integrates tools for a model

### MCP server

This is the process or service that exposes capabilities.

It may offer:

- `tools/list`
- `tools/call`
- resources
- prompts

### Message protocol

MCP commonly uses JSON-RPC 2.0 as its structural message format.

That introduces fields such as:

- `jsonrpc`
- `id`
- `method`
- `params`

And responses with:

- `result`
- `error`

## Typical minimal flow

A basic flow usually looks like this:

1. the client opens a connection to the server
2. it sends `initialize`
3. the server replies with version and capabilities
4. the client requests `tools/list`
5. the server announces available tools
6. the client calls `tools/call`
7. the server returns a structured result

## Why it matters in this repository

This project compares REST and MCP over the same functional case in order to study:

- what changes in the transport
- what changes in capability discovery
- what remains the same in domain logic
