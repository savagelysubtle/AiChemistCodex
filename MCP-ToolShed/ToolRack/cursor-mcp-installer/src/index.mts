#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";


import {
  installGitMcpServer,
} from "./installer.mjs";



// Add startup logs for debugging - Use console.error for logs on stdio servers
console.error("Starting cursor-mcp-installer-free MCP server..."); // Use stderr

const server = new Server(
  {
    name: "cursor-mcp-installer-free",
    version: "0.1.3", // Ensure this matches package.json
  },
  {
    capabilities: {
      tools: {},
      // Support for listChanged notifications as per PR #247
      notifications: {
        listChanged: true,
      },
    },
  }
);

// Adjust the tool list to include git installation
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "install_mcp_server",
        description: "Install an MCP server from an npm package or local path",
        inputSchema: {
          type: "object",
          properties: {
            spec: {
              type: "string",
              description: "The npm package name or local path of the MCP server",
            },
            args: {
              type: "array",
              items: { type: "string" },
              description: "Additional arguments to pass to the server",
            },
            env: {
              type: "array",
              items: { type: "string" },
              description: "Environment variables to set for the server (e.g., KEY=VALUE)",
            },
          },
          required: ["spec"],
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  switch (request.params.name) {
    case "install_mcp_server": {
      const { spec } = request.params.arguments as {
       spec: string;
       args?: string[]; // Keep in schema but not used in destructuring here
       env?: string[]; // Keep in schema but not used in destructuring here
     };
     try {
       // Pass args and env directly from request.params.arguments
       // Pass args and env directly from request.params.arguments, providing defaults if arguments is undefined
       await installGitMcpServer(spec, Array.isArray(request.params.arguments?.args) ? request.params.arguments.args : [], Array.isArray(request.params.arguments?.env) ? request.params.arguments.env : []);
       if (process.env.SMITHERY_CONTAINER !== "true") {
         server.sendToolListChanged();
       }
       return {
         content: [{ type: "text", text: `Successfully installed MCP server: ${spec}` }],
       };
     } catch (error: any) {
       return {
         content: [{ type: "text", text: `Error installing MCP server ${spec}: ${error.message}` }],
         isError: true,
       };
     }
   }
   default:
     return {
       content: [{ type: "text", text: `Unknown tool: ${request.params.name}` }],
       isError: true,
     };
 }
});

async function runServer() {
  // Use console.error for diagnostic messages in stdio servers
  console.error("Initializing MCP server transport...");
  const transport = new StdioServerTransport();
  console.error("Connecting MCP server...");
  await server.connect(transport);
  console.error("MCP server connected and ready"); // Log connection success to stderr
}

runServer().catch((error) => {
  // This already correctly uses console.error
  console.error("Error starting MCP server:", error);
  process.exit(1);
});
