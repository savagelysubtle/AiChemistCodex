1) globally install the library of interest (for example below for the file system MCP)
 npm install -g @modelcontextprotocol/server-filesystem

2) update your config file to use node instead of npx (mine below)

{
  "mcpServers": {
    "filesystem": {
      "command": "C:\\Program Files\\nodejs\\node.exe",
      "args": [
        "C:\\Users\\Steve\\AppData\\Roaming\\npm\\node_modules\\@modelcontextprotocol\\server-filesystem\\dist\\index.js",
        "D:\\Coding\\TheToolShed\\ToolRack"
      ]
    }
  }
}

Hope this helps people I'll post this on Reddit too