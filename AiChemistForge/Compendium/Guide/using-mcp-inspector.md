# Using the MCP Inspector for Local Server Development

The Model Context Protocol (MCP) Inspector is an interactive developer tool essential for testing and debugging MCP servers. It allows you to connect to your server, view its capabilities (resources, tools, prompts), and interact with them directly. This guide focuses on using the Inspector with a locally developed TypeScript/Node.js MCP server, using the `brave-search` server from your `ToolRack` as a specific example.

Reference: [Official MCP Inspector Documentation](https://modelcontextprotocol.io/docs/tools/inspector)

## 1. Launching the MCP Inspector

The Inspector runs directly using `npx` without requiring a separate installation. Open your terminal and run:

```bash
npx @modelcontextprotocol/inspector
```

This command will download (if not already cached) and run the latest version of the Inspector, opening its UI in a new window.

## 2. Configuring for a Local TypeScript/Node.js Server

Once the Inspector UI is open, you need to configure it to start and connect to your local MCP server. Here's how to do it for your `brave-search` server:

*   **Locate the Server Connection Pane:** This is usually the main view when the Inspector starts.
*   **Transport:** Ensure "stdio" is selected, as your `brave-search` server communicates over standard input/output.
*   **Server Startup Configuration:**
    *   **Command:** `node`
    *   **Arguments:** `D:/Coding/TheToolShed/ToolRack/brave-search/dist/index.js`
        *   *This is the path to the compiled JavaScript entry point of your `brave-search` server.*
    *   **Working Directory (CWD):** `D:/Coding/TheToolShed/ToolRack/brave-search/`
        *   *Setting the CWD ensures that your server, which uses `dotenv/config`, can correctly locate its `.env` file if the `BRAVE_API_KEY` is stored there and not overridden by the Inspector's environment variable setting.*
    *   **Environment Variables:** This is the recommended way to provide secrets like API keys to your server when using the Inspector.
        *   Click to add a new environment variable.
        *   **Name:** `BRAVE_API_KEY`
        *   **Value:** `YOUR_BRAVE_API_KEY_HERE` (Replace this with your actual Brave Search API key. You can find this in your `.env.local` file within the `brave-search` project or retrieve it from the [Brave Search Developer Portal](https://search.brave.com/api/)).

*   **Connect:** After filling in these details, click the "Connect" or "Start Server" button.

The Inspector will attempt to launch your `brave-search` server with these settings.

## 3. Inspector UI Overview

Once connected, the Inspector presents several tabs:

*   **Server:** Shows information about the connected server, its capabilities, and connection logs.
*   **Resources:** Lists resources exposed by the server. You can view their metadata and content. (Your `brave-search` server might not expose many explicit resources, as its primary function is tools).
*   **Tools:** Lists all tools the server provides. You can see their input schemas and execute them. This is where you'll find `brave_web_search` and `brave_code_search`.
*   **Prompts:** Lists any prompt templates defined by the server.
*   **Notifications:** Displays all logs (`stderr`) and notifications sent by the server. This is very useful for seeing debug messages from your `logger.ts`.

## 4. Example: Testing the `brave_web_search` Tool

1.  Navigate to the **Tools** tab in the Inspector.
2.  You should see `brave_web_search` and `brave_code_search` listed.
3.  Select `brave_web_search`. The Inspector will display its description and input schema.
4.  **Input Arguments:**
    *   You'll see fields for `query` (string, required), `count` (number, optional), and `offset` (number, optional).
    *   Enter a search term in the `query` field, for example: `MCP Inspector guide`.
    *   You can leave `count` and `offset` at their defaults or specify values (e.g., `count: 5`).
5.  Click the **Execute** or **Call Tool** button.
6.  **Results:**
    *   The Inspector will send the `tools/call` request to your server.
    *   The server will process the request, call the Brave Search API, and send back the results.
    *   The results (a list of text content containing search snippets) will be displayed in the Inspector.
    *   Check the **Notifications** tab as well to see any log messages your server printed during the execution of the tool.

You can similarly test `brave_code_search`.

## 5. Troubleshooting & Tips

*   **Check `BRAVE_API_KEY`:** Most issues with the `brave-search` server will stem from an incorrect or missing `BRAVE_API_KEY`. Double-check it in the Inspector's environment variable settings.
*   **Server Logs:** The **Notifications** tab is your best friend for debugging. Your `logger.ts` sends output here. Look for messages like "API Key check after dotenv" or any error messages.
*   **Server Not Starting:** If the server doesn't start, ensure the path to `dist/index.js` is correct and that the server has been built (e.g., by running `npm run build` or `pnpm build` within the `ToolRack/brave-search` directory if you made recent changes to the TypeScript source).
*   **Inspector Version:** If you encounter strange issues, try updating the inspector: `npx @modelcontextprotocol/inspector@latest ...`
*   **Restart:** Sometimes, simply disconnecting and reconnecting in the Inspector, or restarting the Inspector and server, can resolve transient issues.
*   **Stdio Mode:** Remember that the server communicates via `stdin`/`stdout`. Logs go to `stderr`, which the Inspector captures in the Notifications pane. Ensure your server logic doesn't inadvertently write to `stdout` outside of MCP messages. Your `logger.ts` correctly uses `process.stderr.write`.

This guide should help you effectively use the MCP Inspector to test and debug your `brave-search` server and other MCP servers you develop.