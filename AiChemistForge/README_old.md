# 🛠️ AiChemist Forge: A Workspace for MCP Development

Welcome to the MCP ToolShed, a collection of resources, tools, SDKs, and configurations focused on building and interacting with Model Context Protocol (MCP) servers. This workspace serves as a development environment and reference hub for various MCP-related projects.

## 📁 Workspace Structure

The workspace is organized into several key directories:

*   **`Compendium/`**: A collection of documentation, guides, SDK information, and manuals for the tools and concepts used within this workspace. Think of this as the library or reference section.
*   **`ToolRack/`**: Holds the actual implementations of various MCP tools. These are standalone servers providing specific functionalities (e.g., Brave Search integration, local file system access). These are the ready-to-use tools built with the SDKs from the `ToolBox`.
*   **`.vscode/`, `.cursor/`, `.roo/`**: IDE-specific configuration and metadata files.
*   **`.gitignore`, `.env.local`**: Standard Git ignore file and local environment variable configuration.

## 🚀 Getting Started

2.  **Examine the `ToolRack/`**: Look at the existing tool implementations for examples of how to use the SDKs and structure MCP servers. Each tool should have its own `README.md` explaining its function, setup, and usage.
3.  **Consult the `Compendium/`**: Refer to the documentation here for SDK details, tool guides, and general MCP concepts.
4.  **Set up Environment**: Many tools and SDKs require specific environment variables (like API keys). Ensure you have a `.env.local` file at the root or configure environment variables as required by individual components. Follow setup instructions within each tool/SDK directory. For Python projects, note the preference for using `uv` as per the `801-python-environment` rule.

## 🧭 Available Tools (in the `ToolRack/`)

This section provides a quick overview of the MCP tools currently available in the `ToolRack/`. See the respective `README.md` files within each tool's directory for full details.

*   **Brave Search (`brave-search`)**
    *   **Language:** TypeScript (likely, based on `Compendium/brave-search/README.md`)
    *   **Description:** Provides MCP tools (`brave_web_search`, `brave_local_search`) to interact with the Brave Search API.
    *   **Location:** `ToolRack/brave-search/` *(Assuming it mirrors Compendium)*
*   **Cursor MCP Installer (`cursor-mcp-installer`)**
    *   **Language:** TypeScript (Node.js/`mjs`)
    *   **Description:** An MCP tool to help install and manage other MCP servers within the Cursor IDE environment.
    *   **Location:** `ToolRack/cursor-mcp-installer/` *(Assuming it mirrors Compendium)*
*   **Local File Inspector (`local-file-ingest`)**
    *   **Language:** Python
    *   **Description:** An MCP server allowing inspection of local files and directories (listing, reading).
    *   **Key Features:** Directory tree view, file reading, secure path handling.
    *   **Package Name:** `mcp-local-file-inspector`
    *   **Location:** `ToolRack/local-file-ingest/`
*   **Windows CLI Tool (`win-cli-tool`)**
    *   **Language:** TypeScript (likely)
    *   **Description:** (Assumed based on name) An MCP tool for executing Windows command-line operations.
    *   **Location:** `ToolRack/win-cli-tool/`
*   **Web Crawler (`web-crawler`)**
     *   **Language:** (Unknown from structure)
     *   **Description:** (Assumed based on name) An MCP tool for crawling web pages.
     *   **Location:** `ToolRack/web-crawler/`


*(Note: Details for some tools are inferred from directory names. Please update with accurate information.)*

## 🤝 Contributing

*(Placeholder: Add guidelines here if collaboration is expected. E.g., coding standards, pull request process, issue tracking.)*

## 📜 License

*(Placeholder: Specify the license for the overall workspace or note that individual components may have their own licenses.)*

