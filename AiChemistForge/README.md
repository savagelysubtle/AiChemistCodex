# 🧪 AiChemist Forge

A unified workspace for developing Model Context Protocol (MCP) servers with organized tooling for AI development workflows.

## 🏗️ Architecture

This workspace provides a clean, unified approach to MCP server development with separate implementations for different runtime environments:

- **Python Servers** (`ToolRack/Python/`) - Unified Python MCP server with organized tools
- **TypeScript Servers** (`ToolRack/typescript/`) - TypeScript/Node.js MCP implementations
- **Planning & Documentation** (`Plans/`, `Compendium/`) - Architecture plans and guides

## 🚀 Quick Start

### Python Unified MCP Server
```bash
cd ToolRack/Python
uv sync --all-groups
uv run unified-mcp-server
```

### Development
```bash
# Test the Python server
cd ToolRack/Python
python test_server.py

# View detailed architecture plans
cat Plans/Python/unified_mcp_server_refactor.md
```

## 📁 Workspace Structure

```
AiChemistForge/
├── ToolRack/                    # Production MCP servers
│   ├── Python/                  # Unified Python MCP server
│   │   ├── src/unified_mcp_server/  # Server implementation
│   │   ├── pyproject.toml       # Python dependencies & config
│   │   └── README.md            # Python server documentation
│   └── typescript/              # TypeScript MCP implementations
├── Plans/                       # Architecture & implementation plans
│   └── Python/                  # Python server planning docs
├── Compendium/                  # Documentation & guides
├── .cursor/                     # Workspace documentation & rules
└── README.md                    # This file
```

## 🛠️ Available Tools

### Python Unified Server
**Status: 85% Complete (Phase 3 of 5)**

- ✅ **Database Tools**: Cursor IDE state management, project queries
- ✅ **Resources**: Cursor project discovery and data access
- ✅ **Prompts**: Analysis prompts for project exploration
- 🚧 **Filesystem Tools**: Local file operations (Phase 4 - in progress)
- 📋 **Advanced Features**: Planned for Phase 5

### Tool Categories
- **Database** (`tools/database/`): Database query and management tools
- **Filesystem** (`tools/filesystem/`): Secure file system operations
- **Analysis** (`prompts/analysis/`): AI-powered analysis prompts
- **Resources** (`resources/cursor/`): Structured data access

## 🔧 Configuration

### Environment Variables
```bash
# Server Configuration
export MCP_SERVER_NAME="aichemist-forge"
export MCP_LOG_LEVEL="INFO"
export MCP_TRANSPORT_TYPE="stdio"

# Tool-Specific Settings
export CURSOR_PATH="/path/to/cursor"
export PROJECT_DIRS="/path/to/projects"
export MAX_FILE_SIZE="20000000"
```

### MCP Client Configuration
```json
{
  "mcpServers": {
    "aichemist-forge": {
      "command": "uv",
      "args": ["run", "unified-mcp-server"],
      "cwd": "./ToolRack/Python"
    }
  }
}
```

## 📈 Development Status

**Current Phase**: Phase 4 - Filesystem Tools Implementation

- **Phase 1**: ✅ Infrastructure Setup (100% Complete)
- **Phase 2**: ✅ Tool Organization System (100% Complete)
- **Phase 3**: ✅ Cursor Database Tools (100% Complete)
- **Phase 4**: 🚧 Filesystem Tools (In Progress)
- **Phase 5**: 📋 Advanced Features (Planned)

**Latest Test Results:**
- ✅ 1 tool discovered (cursor_db)
- ✅ 1 resource discovered (cursor://projects)
- ✅ 3 prompts discovered (analysis prompts)
- ✅ 87 Cursor projects found and accessible

## 🏛️ Architecture Principles

- **Unified Structure**: Single server per runtime with organized tools
- **Type Safety**: Comprehensive type hints and validation
- **Security First**: Environment-based secrets, input validation
- **Extensibility**: Plugin-style tool registration
- **Maintainability**: Clear separation of concerns

## 📚 Documentation

- **Server Implementation**: [`ToolRack/Python/README.md`](ToolRack/Python/README.md)
- **Architecture Plan**: [`Plans/Python/unified_mcp_server_refactor.md`](Plans/Python/unified_mcp_server_refactor.md)
- **Implementation Guide**: [`Plans/Python/implementation_guide.md`](Plans/Python/implementation_guide.md)
- **Progress Tracking**: [`.cursor/AiChemistForge.md`](.cursor/AiChemistForge.md)

## 🤝 Contributing

1. **Understand Context**: Review architecture plans in `Plans/`
2. **Follow Standards**: Use UV package manager, Ruff formatting, type hints
3. **Security**: Never hard-code secrets, validate all inputs
4. **Testing**: Test changes thoroughly before committing
5. **Documentation**: Update relevant docs with changes

## 📝 License

MIT License - Individual components may have specific licensing terms.

---

**Project Status**: Active Development | **Architecture**: Unified Servers | **Runtime**: Python 3.13+ & TypeScript