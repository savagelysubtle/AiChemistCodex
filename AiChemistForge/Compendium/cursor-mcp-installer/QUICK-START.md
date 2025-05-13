# 🚀 Quick Start Guide

## Common Scenarios

### 1️⃣ "I just want to try an MCP server quickly"

```powershell
# 1. Open your Cursor MCP config
notepad C:\Users\YourUsername\.cursor\mcp.json

# 2. Add this configuration:
{
  "mcpServers": {
    "MCP Installer": {
      "command": "npx",
      "type": "stdio",
      "args": [
        "cursor-mcp-installer-free@0.1.3",
        "index.mjs"
      ]
    }
  }
}

# 3. Restart Cursor
# 4. Use Claude to install any MCP server!
```

### 2️⃣ "I want to develop my own MCP server"

```powershell
# 1. Create your tools directory
mkdir D:\Coding\tools
cd D:\Coding\tools

# 2. Clone the installer
git clone https://github.com/matthewdcage/cursor-mcp-installer.git
cd cursor-mcp-installer
npm install
npm run build

# 3. Configure Cursor (C:\Users\YourUsername\.cursor\mcp.json)
{
  "mcpServers": {
    "MCP Installer": {
      "command": "node",
      "type": "stdio",
      "args": [
        "D:\\Coding\\tools\\cursor-mcp-installer\\lib\\index.mjs"
      ]
    }
  }
}
```

### 3️⃣ "I found a cool MCP server on GitHub"

```powershell
# Example: Installing the Sequential Thinking Tools
<invoke name="mcp_MCP_Installer_install_repo_mcp_server">
  <parameter name="name">@spences10/mcp-sequentialthinking-tools</parameter>
</invoke>

# Example: Installing Obsidian MCP
<invoke name="mcp_MCP_Installer_install_repo_mcp_server">
  <parameter name="name">obsidian-mcp</parameter>
</invoke>
```

### 4️⃣ "I want to use environment variables with my MCP"

```powershell
# Example: Installing dotenvx with environment variables
<invoke name="mcp_MCP_Installer_install_repo_mcp_server">
  <parameter name="name">@dotenvx/mcp-server</parameter>
  <parameter name="env">["DOTENV_KEY=your_key", "NODE_ENV=development"]</parameter>
</invoke>
```

### 5️⃣ "I want to add a local MCP server with custom args"

```powershell
<invoke name="mcp_MCP_Installer_install_local_mcp_server">
  <parameter name="path">D:\Coding\my-mcp-server</parameter>
  <parameter name="args">["--port", "3000", "--config", "custom.json"]</parameter>
</invoke>
```

## 🔍 Troubleshooting

1. **MCP server not showing up?**
   - Restart Cursor
   - Check your `mcp.json` for correct paths
   - Make sure all paths use double backslashes (`\\`)

2. **Installation failing?**
   - Check if Node.js is installed
   - Try running with administrator privileges
   - Check your network connection

3. **Path issues?**
   - Always use absolute paths in `mcp.json`
   - Use double backslashes for Windows paths
   - Verify the paths exist on your system

## 🎯 Next Steps

- Check out the full documentation in `README.md`
- Join the Cursor community
- Share your custom MCP servers!