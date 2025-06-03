# Compendium MCP Tool (formerly AiChemist Compendium)

[![smithery badge](https://smithery.ai/badge/compendium-mcp-tool)](https://smithery.ai/server/compendium-mcp-tool)

An [MCP (Model Context Protocol)](https://modelcontextprotocol.io) server that enables AI assistants to interact with Obsidian vaults, providing tools for reading, creating, editing, and managing notes and tags.

**Repository:** `savagelysubtle/AiChemistCompendium`

## Warning!!!

This MCP has read and write access (if you allow it). **Please back up your Obsidian vault prior to using AiChemist Compendium** to manage your notes. I recommend using Git, but any reliable backup method will work. These tools have been tested but are still in active development.

## Features

- Read and search notes in your vault
- Create new notes and directories
- Edit existing notes
- Move and delete notes
- Manage tags (add, remove, rename)
- Search vault contents

## Requirements

- Node.js 20 or higher (may work on lower versions, but untested)
- An Obsidian vault

## Install

### Installing Manually

Add to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "compendiumTool": {
      "command": "npx",
      "args": ["-y", "compendium-mcp-tool", "/path/to/your/vault1", "/path/to/your/vault2"],
    }
  }
}
```

Replace `/path/to/your/vault` with the absolute path to your Obsidian vault(s). For example, to use the original `docs-obsidian` directory:

* **Windows**: `"D:\\Coding\\AiChemistCodex\\AiChemistCompendium\\docs-obsidian"` (ensure to escape backslashes in JSON)

Restart Claude for Desktop after saving the configuration. You should see the hammer icon appear, indicating the server is connected.

If you have connection issues, check the logs at:

* **macOS**: `~/Library/Logs/Claude/mcp*.log`
* **Windows**: `%APPDATA%\Claude\logs\mcp*.log`

### Installing via Smithery

> **Warning:** I am not affiliated with Smithery. I recommend manual install if you can.

```bash
npx -y @smithery/cli install compendium-mcp-tool --client claude
```

## Development

Navigate to the tool's directory within your `AiChemistForge` workspace:
```bash
cd AiChemistForge/ToolRack/compendium

# Install dependencies
npm install

# Build
npm run build
```

Then add to your Claude Desktop configuration (e.g., `AiChemistForge/.cursor/mcp.json` if using Cursor's project-specific MCP config, or your global `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "compendiumTool": {
      "command": "node",
      "args": [
        "<absolute-path-to-AiChemistForge/ToolRack/compendium>/build/main.js",
        "D:\\\\Coding\\\\AiChemistCodex\\\\AiChemistCompendium\\\\docs-obsidian",
        "/path/to/your/other_vault"
      ],
      "cwd": "<absolute-path-to-AiChemistForge/ToolRack/compendium>"
    }
  }
}
```

Replace `<absolute-path-to-AiChemistForge/ToolRack/compendium>` with the actual absolute path to the `compendium` directory on your system.

## Available Tools

* `read-note` – Read the contents of a note
* `create-note` – Create a new note
* `edit-note` – Edit an existing note
* `delete-note` – Delete a note
* `move-note` – Move a note to a different location
* `create-directory` – Create a new directory
* `search-vault` – Search notes in the vault
* `add-tags` – Add tags to a note
* `remove-tags` – Remove tags from a note
* `rename-tag` – Rename a tag across all notes
* `manage-tags` – List and organize tags
* `list-available-vaults` – List all available vaults (useful for multi-vault setups)

## Documentation

See the `docs` directory for additional guides:

* `creating-tools.md` – Guide for creating new tools
* `tool-examples.md` – Examples of using the available tools

## Security

This server requires access to your Obsidian vault directory. When configuring:

* Only provide the paths you intend to expose
* Review each tool action before approval

## Troubleshooting

1. **Server not showing up**

   * Verify your JSON syntax
   * Confirm vault path is absolute and exists
   * Restart Claude for Desktop

2. **Permission errors**

   * Ensure the vault path is readable/writable
   * Adjust filesystem permissions

3. **Tool execution failures**

   * Check Claude Desktop logs:

     * **macOS**: `~/Library/Logs/Claude/mcp*.log`
     * **Windows**: `%APPDATA%\Claude\logs\mcp*.log`

## License

MIT
