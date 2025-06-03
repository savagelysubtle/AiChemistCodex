# AiChemistForge - TypeScript Brave Search MCP Server

This TypeScript MCP (Model Context Protocol) server provides tools for interacting with the Brave Search API. It allows users to perform web searches and targeted code searches directly through an MCP client like Cursor. This server is designed to be run as a standalone component, though it's part of the larger AiChemistForge project.

## Features

- **Brave Search Integration**: Leverages the Brave Search API for web and code-specific searches.
- **Stdio Transport**: Uses stdio for communication, making it suitable for local development and integration with command-line tools and clients like Cursor.
- **TypeSafe Development**: Written in TypeScript with Zod for schema validation, ensuring robust tool definitions and argument handling.
- **Environment Variable Configuration**: API keys (like `BRAVE_API_KEY`) are managed through `.env` files.
- **Rate Limiting**: Basic client-side rate limiting for Brave Search API calls.
- **Structured Logging**: Includes a simple logger utility that outputs to `stderr` to keep `stdout` clean for JSON-RPC messages.

## Available Tools

Based on `src/tools/braveSearchTools.ts` and `src/server/server.ts`, the server provides the following tools:

-   **`brave_web_search`**:
    *   Description: Performs a general web search using the Brave Search API. Ideal for broad information gathering, news, articles, and recent events. Supports pagination and result count customization.
    *   Input Schema: `query` (string, required), `count` (number, optional, default 10), `offset` (number, optional, default 0).
-   **`brave_code_search`**:
    *   Description: Searches developer-focused sites (Stack Overflow, GitHub, MDN, etc.) using Brave Search. Ideal for finding code snippets, technical documentation, and programming solutions. Supports result count customization.
    *   Input Schema: `query` (string, required), `count` (number, optional, default 10).

## Prerequisites

-   **Node.js and npm/yarn**: Ensure Node.js (which includes npm) is installed. Yarn can also be used if preferred.
-   **Brave Search API Key**: You need a Brave Search API key. This key should be placed in an `.env` file in the `AiChemistForge/ToolRack/TypeScript/` directory.

## Installation & Setup

1.  **Clone the Server Directory (if not already part of a larger clone):**
    If treating this as a standalone project, clone its specific directory or the parent AiChemistForge repository and navigate here.
    ```bash
    # Example if AiChemistForge is cloned:
    # git clone https://github.com/your-username/AiChemistForge.git
    cd AiChemistForge/ToolRack/TypeScript
    ```

2.  **Install Dependencies:**
    Navigate to the `AiChemistForge/ToolRack/TypeScript/` directory (where `package.json` is located) and run:
    ```bash
    npm install
    ```
    or if you use Yarn:
    ```bash
    yarn install
    ```

3.  **Set up Environment Variables:**
    Create an `.env` file in the `AiChemistForge/ToolRack/TypeScript/` directory by copying from `.env.example` (if one exists, or create it manually).
    Add your Brave Search API key to it:
    ```env
    BRAVE_API_KEY=YOUR_ACTUAL_BRAVE_API_KEY_HERE
    LOG_LEVEL=INFO # Optional: Set to DEBUG for more verbose logs
    ```
    The server (`src/tools/braveSearchTools.ts`) explicitly checks for `BRAVE_API_KEY` and will throw an error if it's not found.

4.  **Build the TypeScript Code:**
    Compile the TypeScript source files into JavaScript:
    ```bash
    npm run build
    ```
    This command uses `tsc` (the TypeScript compiler) as defined in `package.json` and outputs the compiled files to the `dist/` directory.

## Usage

### Running the Server

After building the server, you can run it using Node.js:

1.  **Directly with Node.js:**
    ```bash
    npm start
    ```
    This command (defined in `package.json`) executes `node dist/server/server.js` (assuming `server.ts` is your main entry point after build, adjust if it's `index.ts`).
    The server will start, log to `stderr`, and listen for MCP messages on `stdin` and send responses to `stdout`.

    *Self-correction: Based on the `package.json` and common practice, if `dist/index.js` is the main output, then `npm start` might point to `node dist/index.js`. The server logic seems to be in `server.ts`, which likely compiles to `dist/server/server.js`. The user should verify their `"main"` and `"start"` script in `package.json` to confirm the exact command.*
    Given the file `AiChemistForge/ToolRack/TypeScript/dist/Typescript/src/index.js` was provided, it seems the main entry point might be `dist/Typescript/src/index.js` or `dist/index.js` depending on how `tsc` is configured with `rootDir` and `outDir`. The `package.json` has `"main": "dist/index.js"`. Let's assume `dist/index.js` is the primary entry point for `npm start`.

    If your compiled entry point is `dist/server/server.js` as per `server.ts`, you might run:
    ```bash
    node dist/server/server.js
    ```

2.  **During Development (with auto-rebuild and restart):**
    ```bash
    npm run dev
    ```
    This script (if configured in `package.json`, typically using `nodemon` and `tsc -w`) will watch for file changes, recompile, and restart the server automatically.

### Connecting from an MCP Client (e.g., Cursor)

To connect this TypeScript MCP server to a client like Cursor:

1.  **Cursor Settings:**
    Navigate to `Features > Model Context Protocol` in Cursor's settings.

2.  **Add Server Configuration:**
    *   **Command:** This should be the command to run your compiled JavaScript server. Node.js must be in the system's PATH.
        Example: `node D:\\Coding\\AiChemistCodex\\AiChemistForge\\ToolRack\\TypeScript\\dist\\index.js` (Adjust the path and entry point file as necessary).
        Or, if you create a batch/shell script to launch it (recommended for consistency):
        `D:\\Coding\\AiChemistCodex\\AiChemistForge\\ToolRack\\TypeScript\\start_ts_server.bat` (You'd need to create this script).
    *   **CWD (Current Working Directory):** Absolute path to the `ToolRack/TypeScript/` directory (e.g., `D:\\Coding\\AiChemistCodex\\AiChemistForge\\ToolRack\\TypeScript`).

    Example JSON for Cursor settings:
    ```json
    {
      "mcpServers": {
        "aichemistforge-ts-brave-server": { // Choose a unique name
          "command": "node D:\\path\\to\\AiChemistForge\\ToolRack\\TypeScript\\dist\\index.js", // Or path to your start script
          "cwd": "D:\\path\\to\\AiChemistForge\\ToolRack\\TypeScript"
        }
      }
    }
    ```
    **Note:**
    *   Replace `D:\\path\\to\\` with the actual absolute path.
    *   Use double backslashes (`\\`) for paths in JSON on Windows.
    *   Ensure Node.js is accessible from the environment where Cursor executes commands.

## Development

### Project Structure
Key files and directories within `ToolRack/TypeScript/`:

-   `package.json`: Defines project metadata, dependencies, and npm scripts.
-   `tsconfig.json`: Configuration for the TypeScript compiler.
-   `.env` / `.env.example`: For environment variables like API keys.
-   `src/`: Contains the TypeScript source code.
    -   `server.ts` (or `index.ts`): The main entry point for the MCP server application, responsible for initializing `McpServer`, registering tools, and connecting the transport.
    -   `tools/braveSearchTools.ts`: Defines the Brave Search tool schemas (`BraveWebSearchShape`, `BraveCodeSearchShape`), tool metadata (`WEB_SEARCH_TOOL`, `CODE_SEARCH_TOOL`), and the core logic for executing searches (`executeWebSearch`, `executeCodeSearch`).
    -   `utils/logger.ts`: A simple logging utility to direct logs to `stderr`.
-   `dist/`: Output directory for compiled JavaScript files and source maps, generated by `npm run build`.

### Adding New Tools

1.  **Define Tool Logic and Schema (e.g., in a new `src/tools/myNewTool.ts` file):**
    ```typescript
    import { z, ZodRawShape } from 'zod';
    import { Tool, CallToolResult, TextContent } from "@modelcontextprotocol/sdk/types.js";
    import { log } from '../utils/logger.js'; // Your logger

    // 1. Define Zod Shape for input schema (used by McpServer.tool)
    export const MyNewToolShape: ZodRawShape = {
      inputParam: z.string().describe("An example input parameter"),
    };

    // 2. Define Zod Schema instance (for type inference)
    export const MyNewToolZodSchema = z.object(MyNewToolShape);

    // 3. Define the Tool metadata object
    export const MY_NEW_TOOL: Tool = {
      name: "my_new_tool",
      description: "This is a new example tool.",
      inputSchema: { // Plain object schema for Tool type compatibility
        type: "object",
        properties: {
          inputParam: { type: "string", description: "An example input parameter" },
        },
        required: ["inputParam"],
      },
      // ... other annotations if needed
    };

    // 4. Define the execution function
    export async function executeMyNewTool(
      args: z.infer<typeof MyNewToolZodSchema>
    ): Promise<CallToolResult> {
      log('info', `Executing my_new_tool with: ${args.inputParam}`);
      try {
        // Your tool logic here
        const resultText = `Processed: ${args.inputParam.toUpperCase()}`;
        return {
          content: [{ type: "text", text: resultText } as TextContent],
          isError: false,
        };
      } catch (error) {
        log('error', `Error in my_new_tool: ${error}`);
        return {
          content: [{ type: "text", text: `Error: ${error instanceof Error ? error.message : String(error)}` } as TextContent],
          isError: true,
        };
      }
    }
    ```

2.  **Register the Tool in `src/server.ts` (or your main server file):**
    -   Import the new tool's metadata, Zod shape, and execution function.
    -   In the `main` function of your server, register it using `server.tool()`:
        ```typescript
        // ... other imports
        import {
          MY_NEW_TOOL,
          executeMyNewTool,
          MyNewToolShape // ZodRawShape
        } from './tools/myNewTool.js';

        // Inside async function main():
        // ... server initialization ...

        log('info', `Registering tool: ${MY_NEW_TOOL.name}`);
        server.tool(
          MY_NEW_TOOL.name,
          MyNewToolShape, // Pass the ZodRawShape for schema
          (args: unknown) => wrapToolExecution(MY_NEW_TOOL.name, executeMyNewTool, args) // Use your wrapper if you have one
          // Or directly: async (args: z.infer<typeof MyNewToolZodSchema>) => executeMyNewTool(args)
        );
        ```

3.  **Rebuild:**
    Run `npm run build` to compile the changes.

## License
This project is typically licensed under an open-source license (e.g., MIT). Refer to the `LICENSE` file in the root of the AiChemistForge repository for specific details.

## Support
For issues, questions, or contributions, please refer to the issue tracker or contribution guidelines of the parent AiChemistForge project.