process.stderr.write('SERVER.TS TOP OF FILE\n');
process.stderr.write(`SERVER.TS CWD AT VERY START: ${process.cwd()}\n`);
process.stderr.write(`SERVER.TS BRAVE_API_KEY AT VERY START: ${process.env.BRAVE_API_KEY || 'UNDEFINED'}\n`);

import 'dotenv/config';
// Simple Logger Utility
// const log = (level: 'info' | 'error' | 'warn' | 'debug', message: string, ...args: any[]) => {
//   const timestamp = new Date().toISOString();
//   const logMethod = level === 'error' ? console.error : level === 'warn' ? console.warn : console.log;
//   logMethod(`[${timestamp}] [${level.toUpperCase()}] ${message}`, ...args);
// };
import { log } from '../utils/logger.js'; // Import the logger

// --- Debugging Logs ---
log('warn', `MCP Server Starting. CWD: ${process.cwd()}`);
// ----------------------

log('info', "dotenv/config imported.");
// --- Debugging Logs ---
log('warn', `API Key check after dotenv: ${process.env.BRAVE_API_KEY ? 'LOADED' : 'MISSING'}`);
// ----------------------
log('info', `BRAVE_API_KEY from process.env after dotenv: ${process.env.BRAVE_API_KEY ? 'Loaded' : 'NOT LOADED'}`);

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolResult, TextContent } from "@modelcontextprotocol/sdk/types.js"; // Import types for wrapper
// No need to import ToolSchema if we are not casting to it.

// Import the tool definitions and their separate execution functions
import {
  WEB_SEARCH_TOOL,
  CODE_SEARCH_TOOL,
  executeWebSearch,
  executeCodeSearch,
  BraveWebSearchShape, // Import ZodRawShape
  BraveCodeSearchShape // Import ZodRawShape
} from '../tools/braveSearchTools.js';

log('info', "Imported from ../tools/braveSearchTools.js");

// Helper function to wrap tool execution with logging
async function wrapToolExecution(
  toolName: string,
  executor: (args: any) => Promise<CallToolResult>,
  args: unknown
): Promise<CallToolResult> {
  log('info', `Executing tool: ${toolName}`, { args }); // Log args too
  try {
    const result = await executor(args as any);
    if (result.isError) {
      log('warn', `Tool ${toolName} finished with error.`, { result });
    } else {
      log('info', `Tool ${toolName} finished successfully.`); // Avoid logging potentially large results unless debugging
      // log('debug', `Tool ${toolName} result:`, { result }); // Optional: Add if needed for debugging
    }
    return result;
  } catch (executionError) {
    // This catches errors *thrown* by the executor, which shouldn't happen
    // if it follows the pattern of returning { isError: true, ... }
    log('error', `Unexpected error thrown during ${toolName} execution:`, executionError);
    return {
      content: [{ type: "text", text: `Unexpected server error during ${toolName}: ${executionError instanceof Error ? executionError.message : String(executionError)}` } as TextContent],
      isError: true,
    };
  }
}


async function main() {
  log('info', "Starting Brave Search MCP Server...");

  try {
    const server = new McpServer({
      name: "BraveSearchServer",
      version: "0.1.4", // Increment version
      description: "MCP Server providing Brave Search tools.",
      capabilities: {
        resources: {},
        // Tools are registered via server.tool(), so no need to declare them here.
      }
    });

    log('info', `Registering tool: ${WEB_SEARCH_TOOL.name}`);
    server.tool(
      WEB_SEARCH_TOOL.name,
      BraveWebSearchShape, // Use the ZodRawShape directly
      (args: unknown) => wrapToolExecution(WEB_SEARCH_TOOL.name, executeWebSearch, args)
    );

    log('info', `Registering tool: ${CODE_SEARCH_TOOL.name}`);
    server.tool(
      CODE_SEARCH_TOOL.name,
      BraveCodeSearchShape, // Use the ZodRawShape directly
      (args: unknown) => wrapToolExecution(CODE_SEARCH_TOOL.name, executeCodeSearch, args)
    );

    log('info', `All tools registered.`);

    const transport = new StdioServerTransport();
    log('info', "Connecting to transport...");
    await server.connect(transport);

    log('info', "Brave Search MCP Server connected and listening on stdio.");

  } catch (error) {
    // console.error("Failed to start or run Brave Search MCP Server:", error); // Old log
    log('error', "Failed to start or run Brave Search MCP Server:", error);
    if (error instanceof Error && error.stack) {
      // console.error("Stack trace:", error.stack); // Old log
      log('error', "Stack trace:", error.stack);
    }
    process.exit(1);
  }
}

main().catch(error => {
  // console.error("Unhandled error in main async function execution:", error); // Old log
  log('error', "Unhandled error in main async function execution:", error);
  if (error instanceof Error && error.stack) {
    // console.error("Stack trace:", error.stack); // Old log
    log('error', "Stack trace:", error.stack);
  }
  process.exit(1);
});
