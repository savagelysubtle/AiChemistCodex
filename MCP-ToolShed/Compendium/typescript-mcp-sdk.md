# TypeScript MCP SDK Documentation

## What is the TypeScript MCP SDK?

The TypeScript MCP SDK (Model Context Protocol Software Development Kit) is a comprehensive toolkit that implements the full MCP specification, enabling developers to build applications that can communicate with Large Language Models (LLMs) in a standardized way. It provides a structured approach to separating the concerns of providing context from the actual LLM interaction.

The SDK is designed to be flexible and powerful, allowing developers to create both MCP clients that connect to any MCP server and MCP servers that expose resources, tools, and prompts to LLM applications.

## Key Features and Capabilities

### Core Functionality

- **Full MCP Specification Implementation**: Implements the complete Model Context Protocol specification
- **Bidirectional Support**: Create both MCP clients and servers with the same SDK
- **Multiple Transport Options**: Support for stdio (command-line) and SSE (Server-Sent Events over HTTP) communication
- **Comprehensive Type Safety**: Built with TypeScript for robust type checking and developer experience

### Server Capabilities

- **Resources**: Expose data to LLMs through standardized resource interfaces
- **Tools**: Provide functionality that LLMs can use to perform actions
- **Prompts**: Define reusable templates for LLM interactions
- **Connection Management**: Handle client connections and message routing
- **Protocol Compliance**: Ensure adherence to the MCP specification

### Client Capabilities

- **Resource Access**: Read data from MCP servers
- **Tool Invocation**: Call tools provided by MCP servers
- **Prompt Retrieval**: Get and use prompt templates
- **Transport Management**: Connect to servers using different transport mechanisms

## Installation and Setup

### Prerequisites

- Node.js (v14 or later recommended)
- npm or yarn

### Installation

```bash
npm install @modelcontextprotocol/sdk
```

### Basic Server Setup

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

// Create an MCP server
const server = new McpServer({
  name: "Example Server",
  version: "1.0.0"
});

// Add a simple tool
server.tool("add",
  { a: z.number(), b: z.number() },
  async ({ a, b }) => ({
    content: [{ type: "text", text: String(a + b) }]
  })
);

// Start the server using stdio transport
const transport = new StdioServerTransport();
await server.connect(transport);
```

### Basic Client Setup

```typescript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

// Create a transport to connect to a server
const transport = new StdioClientTransport({
  command: "node",
  args: ["server.js"]
});

// Create an MCP client
const client = new Client(
  {
    name: "Example Client",
    version: "1.0.0"
  },
  {
    capabilities: {
      prompts: {},
      resources: {},
      tools: {}
    }
  }
);

// Connect to the server
await client.connect(transport);

// Now you can interact with the server
const result = await client.callTool({
  name: "add",
  arguments: { a: 5, b: 3 }
});
```

## Usage Examples

### Creating Resources

Resources in MCP are similar to GET endpoints in a REST API. They provide data but shouldn't perform significant computation or have side effects.

#### Static Resource

```typescript
server.resource(
  "config",
  "config://app",
  async (uri) => ({
    contents: [{
      uri: uri.href,
      text: "App configuration here"
    }]
  })
);
```

#### Dynamic Resource with Parameters

```typescript
server.resource(
  "user-profile",
  new ResourceTemplate("users://{userId}/profile", { list: undefined }),
  async (uri, { userId }) => ({
    contents: [{
      uri: uri.href,
      text: `Profile data for user ${userId}`
    }]
  })
);
```

### Creating Tools

Tools let LLMs take actions through your server. Unlike resources, tools are expected to perform computation and have side effects.

#### Simple Tool

```typescript
server.tool(
  "calculate-bmi",
  {
    weightKg: z.number(),
    heightM: z.number()
  },
  async ({ weightKg, heightM }) => ({
    content: [{
      type: "text",
      text: String(weightKg / (heightM * heightM))
    }]
  })
);
```

#### Async Tool with External API Call

```typescript
server.tool(
  "fetch-weather",
  { city: z.string() },
  async ({ city }) => {
    const response = await fetch(`https://api.weather.com/${city}`);
    const data = await response.text();
    return {
      content: [{ type: "text", text: data }]
    };
  }
);
```

### Creating Prompts

Prompts are reusable templates that help LLMs interact with your server effectively.

```typescript
server.prompt(
  "review-code",
  { code: z.string() },
  ({ code }) => ({
    messages: [{
      role: "user",
      content: {
        type: "text",
        text: `Please review this code:\n\n${code}`
      }
    }]
  })
);
```

### Running a Server with HTTP/SSE Transport

For remote servers, you can use HTTP with Server-Sent Events (SSE):

```typescript
import express from "express";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";

const server = new McpServer({
  name: "example-server",
  version: "1.0.0"
});

// Set up server resources, tools, and prompts...

const app = express();
const transports = {};

app.get("/sse", async (_, res) => {
  const transport = new SSEServerTransport('/messages', res);
  transports[transport.sessionId] = transport;
  res.on("close", () => {
    delete transports[transport.sessionId];
  });
  await server.connect(transport);
});

app.post("/messages", async (req, res) => {
  const sessionId = req.query.sessionId;
  const transport = transports[sessionId];
  if (transport) {
    await transport.handlePostMessage(req, res);
  } else {
    res.status(400).send('No transport found for sessionId');
  }
});

app.listen(3001);
```

## API Reference

### Server Classes

- **McpServer**: High-level server implementation with simplified API
- **Server**: Low-level server implementation with direct request handling
- **StdioServerTransport**: Transport for command-line communication
- **SSEServerTransport**: Transport for HTTP/SSE communication

### Client Classes

- **Client**: High-level client implementation
- **StdioClientTransport**: Transport for connecting to stdio servers
- **SSEClientTransport**: Transport for connecting to HTTP/SSE servers

### Resource Handling

- **ResourceTemplate**: Template for dynamic resources with parameters
- **Resource**: Interface for resource definitions

### Tool Handling

- **Tool**: Interface for tool definitions
- **ToolSchema**: Schema for tool input validation

### Prompt Handling

- **Prompt**: Interface for prompt definitions
- **PromptSchema**: Schema for prompt input validation

## Advanced Usage

### Low-Level Server Implementation

For more control, you can use the low-level Server class directly:

```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  ListPromptsRequestSchema,
  GetPromptRequestSchema
} from "@modelcontextprotocol/sdk/types.js";

const server = new Server(
  {
    name: "example-server",
    version: "1.0.0"
  },
  {
    capabilities: {
      prompts: {}
    }
  }
);

server.setRequestHandler(ListPromptsRequestSchema, async () => {
  return {
    prompts: [{
      name: "example-prompt",
      description: "An example prompt template",
      arguments: [{
        name: "arg1",
        description: "Example argument",
        required: true
      }]
    }]
  };
});

server.setRequestHandler(GetPromptRequestSchema, async (request) => {
  if (request.params.name !== "example-prompt") {
    throw new Error("Unknown prompt");
  }
  return {
    description: "Example prompt",
    messages: [{
      role: "user",
      content: {
        type: "text",
        text: "Example prompt text"
      }
    }]
  };
});

const transport = new StdioServerTransport();
await server.connect(transport);
```

## Testing and Debugging

To test your MCP servers, you can use the [MCP Inspector](https://github.com/modelcontextprotocol/inspector), a tool designed specifically for testing and debugging MCP servers.

## Official Documentation and Resources

- [Model Context Protocol Documentation](https://modelcontextprotocol.io)
- [MCP Specification](https://spec.modelcontextprotocol.io)
- [Example Servers Repository](https://github.com/modelcontextprotocol/servers)
- [TypeScript SDK Repository](https://github.com/modelcontextprotocol/typescript-sdk)

## License

The TypeScript MCP SDK is licensed under the MIT License, making it freely available for both personal and commercial use.
