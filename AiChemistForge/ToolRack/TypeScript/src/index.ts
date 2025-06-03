import * as dotenv from 'dotenv';
dotenv.config(); // Load environment variables from .env file

// IMPORTANT: Ensure this custom logger is configured to output to stderr
// to keep stdout clean for JSON-RPC communication.
import { log } from './utils/logger.js';

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from 'zod'; // For schema definitions if needed for tools

// Import tool definitions, handlers, and Zod schemas
import {
  WEB_SEARCH_TOOL,
  CODE_SEARCH_TOOL,
  executeWebSearch,
  executeCodeSearch,
  BraveWebSearchShape,      // Import Zod SHAPE
  BraveCodeSearchShape,     // Import Zod SHAPE
  BraveWebSearchZodSchema,  // Import Zod SCHEMA INSTANCE for infer
  BraveCodeSearchZodSchema  // Import Zod SCHEMA INSTANCE for infer
} from './tools/braveSearchTools.js';

async function main() {
  console.error("[TS_SERVER_LOG] Initializing MyTypeScriptMCPServer...");
  const server = new McpServer({
    name: "MyTypeScriptMCPServer",
    version: "0.1.0",
  });
  console.error("[TS_SERVER_LOG] McpServer instance created.");

  console.error("[TS_SERVER_LOG] Registering tools...");
  // Register Brave Search Web Tool
  if (WEB_SEARCH_TOOL && BraveWebSearchShape && BraveWebSearchZodSchema) {
    server.tool(
      WEB_SEARCH_TOOL.name,
      BraveWebSearchShape, // Pass the Zod SHAPE here
      async (args: z.infer<typeof BraveWebSearchZodSchema>) => executeWebSearch(args)
    );
    // Use console.error for server operational logs, or ensure 'log' function directs to stderr
    console.error(`[TS_SERVER_LOG] Registered tool: ${WEB_SEARCH_TOOL.name}`);
  } else {
    console.error("[TS_SERVER_LOG] WEB_SEARCH_TOOL or its Zod shape/schema is undefined. Tool not registered.");
  }

  // Register Brave Code Search Tool
  if (CODE_SEARCH_TOOL && BraveCodeSearchShape && BraveCodeSearchZodSchema) {
    server.tool(
      CODE_SEARCH_TOOL.name,
      BraveCodeSearchShape, // Pass the Zod SHAPE here
      async (args: z.infer<typeof BraveCodeSearchZodSchema>) => executeCodeSearch(args)
    );
    console.error(`[TS_SERVER_LOG] Registered tool: ${CODE_SEARCH_TOOL.name}`);
  } else {
    console.error("[TS_SERVER_LOG] CODE_SEARCH_TOOL or its Zod shape/schema is undefined. Tool not registered.");
  }
  console.error("[TS_SERVER_LOG] Tool registration complete.");

  const transport = new StdioServerTransport();
  console.error("[TS_SERVER_LOG] StdioServerTransport created. Attempting to connect...");
  try {
    await server.connect(transport);
    console.error("[TS_SERVER_LOG] MCP Server connected via Stdio. Waiting for requests...");
  } catch (error) {
    console.error("[TS_SERVER_LOG] Failed to connect MCP server:", error);
    process.exit(1);
  }
}

main().catch((error) => {
  console.error("[TS_SERVER_LOG] Unhandled error in main function:", error);
  process.exit(1);
});