# 🛠️ The MCP Tools Shed 🏚️

Welcome to the MCP Tools Shed - your one-stop-shop for managing and installing Model Context Protocol (MCP) servers in Cursor IDE!

## 📋 Table of Contents
- [Installation Methods](#installation-methods)
  - [Method 1: NPX (No Installation)](#method-1-npx-no-installation)
  - [Method 2: Global NPM Installation](#method-2-global-npm-installation)
  - [Method 3: Local Installation](#method-3-local-installation)
- [Usage Examples](#usage-examples)
- [Adding Tools to Your Shed](#adding-tools-to-your-shed)

## 🔧 Installation Methods

### Method 1: NPX (No Installation)
This is the quickest way to get started without installing anything globally.

1. Open your Cursor MCP configuration file:
   ```
   C:\Users\YourUsername\.cursor\mcp.json
   ```

2. Add this configuration:
   ```json
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
   ```
---

### Method 2: Global NPM Installation
For frequent users, installing globally might be more convenient.

1. Install the package globally:
   ```powershell
   npm install -g cursor-mcp-installer-free@0.1.3
   ```

2. Configure in `C:\Users\YourUsername\.cursor\mcp.json`:
   ```json
   {
     "mcpServers": {
       "MCP Installer": {
         "command": "cursor-mcp-installer-free",
         "type": "stdio",
         "args": [
           "index.mjs"
         ]
       }
     }
   }
   ```
---

### Method 3: Local Installation
For development or customization purposes.

1. Clone to your tools directory:
   ```powershell
   cd D:\Coding\tools
   git clone https://github.com/matthewdcage/cursor-mcp-installer.git
   cd cursor-mcp-installer
   npm install
   npm run build
   ```

2. Configure in `C:\Users\YourUsername\.cursor\mcp.json`:
   ```json
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

## 🚀 Usage Examples

### Example 1: Installing Sequential Thinking Tools
```powershell
# From your workspace (e.g., D:\Coding\my-project)
<invoke name="mcp_MCP_Installer_install_repo_mcp_server">
  <parameter name="name">@spences10/mcp-sequentialthinking-tools</parameter>
</invoke>
```

### Example 2: Installing Obsidian MCP
```powershell
# From D:\Coding\my-project
<invoke name="mcp_MCP_Installer_install_repo_mcp_server">
  <parameter name="name">obsidian-mcp</parameter>
</invoke>
```

### Example 3: Installing a Local MCP Server
```powershell
# If you have a local MCP server at D:\Coding\my-mcp-server
<invoke name="mcp_MCP_Installer_install_local_mcp_server">
  <parameter name="path">D:\Coding\my-mcp-server</parameter>
</invoke>
```

## 🏗️ Adding Tools to Your Shed

Let's say you're working in `D:\Projects\webapp` and found a cool MCP tool you want to add to your shed:

1. **For NPM Packages:**
   ```powershell
   # Add dotenvx MCP server
   <invoke name="mcp_MCP_Installer_install_repo_mcp_server">
     <parameter name="name">@dotenvx/mcp-server</parameter>
   </invoke>
   ```

2. **For Local Development:**
   ```powershell
   # First, clone the repo to your tools directory
   cd D:\Coding\tools
   git clone https://github.com/dotenvx/dotenvx.git
   cd dotenvx
   npm install

   # Then add it to Cursor
   <invoke name="mcp_MCP_Installer_install_local_mcp_server">
     <parameter name="path">D:\Coding\tools\dotenvx</parameter>
   </invoke>
   ```

3. **Custom Configuration:**
   ```powershell
   # Add a custom MCP server configuration
   <invoke name="mcp_MCP_Installer_add_to_cursor_config">
     <parameter name="name">My Custom MCP</parameter>
     <parameter name="command">node</parameter>
     <parameter name="args">["D:\\Coding\\tools\\my-custom-mcp\\server.js"]</parameter>
   </invoke>
   ```

## 🔄 After Installation

1. Restart Cursor IDE to apply changes
2. Your new MCP server will appear in the sidebar
3. Use Claude to interact with your newly installed tools

## 📝 Notes

- Always use double backslashes `\\` in Windows paths when configuring in JSON
- Keep your tools organized in a dedicated directory (e.g., `D:\Coding\tools`)
- Remember to restart Cursor after adding new MCP servers
- Check the server's documentation for specific configuration requirements