<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

## Example `mcp.json` for MCP Server with UV and Python SDK on Windows (Cursor IDE)

To configure Cursor IDE to use an MCP server (Model Context Protocol) written in Python, managed with the [UV package manager](https://python-uv.org/), your `mcp.json` should define the server using the `uv` command. This allows Cursor to launch and communicate with your local MCP server using Python and UV.

Below is a template for what your `.cursor/mcp.json` file should look like for a typical Python MCP server setup on Windows:

```json
{
  "mcpServers": {
    "your-server-name": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Absolute\\Path\\To\\Your\\Project",
        "run",
        "your_server.py"
      ]
    }
  }
}
```

**Key points:**

- Replace `"your-server-name"` with a descriptive name for your server (e.g., `"weather"`, `"screenpipe"`, etc.).
- `"command": "uv"` tells Cursor to use the UV Python package manager to run your server.
- `"--directory", "C:\\Absolute\\Path\\To\\Your\\Project"` should be the absolute path to the folder containing your MCP server code (use double backslashes or a raw string for Windows paths).
- `"run", "your_server.py"` tells UV to run your Python server script (replace `your_server.py` with your actual entry point).
- If you use a module, you can use `"run", "python", "-m", "your_module"` as shown in some examples[^5].

**Example for a project named `weather` in `C:\Users\YourName\weather`:**

```json
{
  "mcpServers": {
    "weather": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Users\\YourName\\weather",
        "run",
        "weather.py"
      ]
    }
  }
}
```


## Additional Notes

- Place this file in either your project directory as `.cursor/mcp.json` (for project-specific servers), or globally at `C:\Users\<YourUser>\.cursor\mcp.json` (for all projects)[^3][^5].
- If your MCP server needs environment variables (like API keys), add an `"env"` block:

```json
"env": {
  "MY_API_KEY": "your-api-key"
}
```

- After editing or creating the file, restart Cursor IDE to load the new configuration[^3][^5].
- Make sure you have installed UV and any required dependencies for your server[^1][^5].


## References to Examples

- The structure above matches official and community examples for Python MCP servers using UV, such as the weather example[^4], Screenpipe[^2], and Semgrep[^6].
- Using `"uv"` is recommended for speed and compatibility with Cursor; alternatives like `pipenv` may not work reliably with Cursor's MCP integration[^4].

This setup allows Cursor IDE to launch and communicate with your Python MCP server using UV on Windows, enabling AI-powered features and integrations.

<div style="text-align: center">⁂</div>

[^1]: https://www.firecrawl.dev/blog/fastmcp-tutorial-building-mcp-servers-python

[^2]: https://docs.screenpi.pe/mcp-server

[^3]: https://apidog.com/blog/connect-api-specifications-mcp-cursor/

[^4]: https://stackoverflow.com/questions/79557164/failed-to-create-client-when-setting-mcp-server-with-cursor-using-pipenv

[^5]: https://www.firecrawl.dev/blog/best-mcp-servers-for-cursor

[^6]: https://github.com/semgrep/mcp

[^7]: https://docs.cursor.com/context/model-context-protocol

[^8]: https://www.youtube.com/watch?v=RkPU7eCG_FM

[^9]: https://apidog.com/blog/build-a-custom-mcp-server/

[^10]: https://www.heroku.com/blog/improved-my-productivity-cursor-and-heroku-mcp-server/

[^11]: https://dev.to/composiodev/how-to-connect-cursor-to-100-mcp-servers-within-minutes-3h74

[^12]: https://www.youtube.com/watch?v=YNe5aYutEPU

[^13]: https://github.com/ContextualAI/contextual-mcp-server

[^14]: https://www.youtube.com/watch?v=xiu1D1bwWp0

[^15]: https://www.arsturn.com/blog/connecting-cursor-with-mcp-servers

[^16]: https://forum.cursor.com/t/how-to-use-mcp-server/50064

[^17]: https://github.com/modelcontextprotocol/python-sdk

[^18]: https://cursor.directory/mcp

