# Unified Python MCP Server Refactoring Plan

## 🎯 Objective
Refactor existing MCP servers into a single, unified Python MCP server with clean separation between server infrastructure and tools, organized by tool type for maintainability and extensibility.

## 📊 Current State Analysis

### Existing Servers
1. **cursor-db-mcp** (723 lines)
   - ✅ Well-structured with FastMCP
   - ✅ Implements resources, tools, and prompts
   - ✅ Uses lifecycle management
   - ❌ Missing `setup_logging` import
   - ❌ All functionality in single file

2. **local-file-ingest**
   - ❌ Incomplete implementation (only `__init__.py`)
   - ❌ No actual server code found

### Current Issues
- Duplicate server infrastructure across projects
- No tool organization by type
- Missing shared utilities
- Inconsistent error handling patterns
- No central configuration management

## 🏗️ Target Architecture

```
ToolRack/Python/src/unified_mcp_server/
├── pyproject.toml                 # Main project configuration
├── uv.lock                       # Dependency lock file
├── README.md                     # Server documentation
├── .env.example                  # Environment template
├── src/
│   └── unified_mcp_server/
│       ├── __init__.py
│       ├── main.py               # Server entry point
│       ├── server/               # Core server infrastructure
│       │   ├── __init__.py
│       │   ├── app.py           # FastMCP app setup
│       │   ├── lifecycle.py     # App lifecycle management
│       │   ├── config.py        # Configuration management
│       │   └── logging.py       # Logging setup
│       ├── tools/               # Tool implementations by type
│       │   ├── __init__.py
│       │   ├── database/        # Database tools
│       │   │   ├── __init__.py
│       │   │   ├── cursor_db.py # Cursor database tools
│       │   │   └── base.py      # Base database tool class
│       │   ├── filesystem/      # File system tools
│       │   │   ├── __init__.py
│       │   │   ├── local_files.py # Local file operations
│       │   │   └── base.py      # Base filesystem tool class
│       │   └── registry.py      # Tool registration system
│       ├── resources/           # MCP Resources by category
│       │   ├── __init__.py
│       │   ├── cursor/          # Cursor-related resources
│       │   │   ├── __init__.py
│       │   │   └── projects.py
│       │   └── registry.py      # Resource registration system
│       ├── prompts/             # MCP Prompts by category
│       │   ├── __init__.py
│       │   ├── analysis/        # Analysis prompts
│       │   │   ├── __init__.py
│       │   │   └── cursor_analysis.py
│       │   └── registry.py      # Prompt registration system
│       └── utils/               # Shared utilities
│           ├── __init__.py
│           ├── exceptions.py    # Custom exceptions
│           ├── validators.py    # Input validation
│           └── security.py      # Security utilities
```

## 🔧 Implementation Plan

### Phase 1: Infrastructure Setup (Priority: HIGH)
**Tasks:**
- [ ] Create unified server directory structure
- [ ] Set up `pyproject.toml` with proper dependencies
- [ ] Implement core server infrastructure (`server/` module)
- [ ] Create logging and configuration systems
- [ ] Set up transport layer (stdio + SSE support)

**Key Files:**
- `server/app.py` - FastMCP application setup
- `server/config.py` - Environment-based configuration
- `server/logging.py` - Structured logging with levels
- `server/lifecycle.py` - App startup/shutdown management

### Phase 2: Tool Organization System (Priority: HIGH)
**Tasks:**
- [ ] Create tool registry system
- [ ] Implement base tool classes by type
- [ ] Define tool interface contracts
- [ ] Create tool discovery mechanism
- [ ] Implement error handling patterns

**Key Files:**
- `tools/registry.py` - Central tool registration
- `tools/database/base.py` - Database tool interface
- `tools/filesystem/base.py` - Filesystem tool interface

### Phase 3: Migrate Cursor Database Tools (Priority: MEDIUM)
**Tasks:**
- [ ] Extract CursorDBManager from existing server
- [ ] Refactor into `tools/database/cursor_db.py`
- [ ] Implement proper error handling and validation
- [ ] Create corresponding resources in `resources/cursor/`
- [ ] Add analysis prompts in `prompts/analysis/`

**Migration Strategy:**
- Extract `CursorDBManager` class → `tools/database/cursor_db.py`
- Convert `@mcp.tool()` functions → Tool class methods
- Move `@mcp.resource()` functions → `resources/cursor/projects.py`
- Move `@mcp.prompt()` functions → `prompts/analysis/cursor_analysis.py`

### Phase 4: Implement File System Tools (Priority: MEDIUM)
**Tasks:**
- [ ] Complete local-file-ingest implementation
- [ ] Create `tools/filesystem/local_files.py`
- [ ] Implement secure path handling
- [ ] Add file operation tools (read, list, search)
- [ ] Create filesystem resources

### Phase 5: Advanced Features (Priority: LOW)
**Tasks:**
- [ ] Implement tool composition patterns
- [ ] Add plugin system for external tools
- [ ] Create tool dependency injection
- [ ] Implement caching layer
- [ ] Add metrics and monitoring

## 🛠️ Tool Categories & Organization

### Database Tools (`tools/database/`)
- **cursor_db.py**: Cursor IDE database operations
  - `query_table()` - Query Cursor state databases
  - `refresh_databases()` - Refresh database connections
  - `add_project_directory()` - Add new project directories

- **Future**: postgresql.py, sqlite.py, mongodb.py

### Filesystem Tools (`tools/filesystem/`)
- **local_files.py**: Local file system operations
  - `list_directory()` - Directory listing with filtering
  - `read_file()` - Secure file reading
  - `search_files()` - File content search
  - `file_stats()` - File metadata

- **Future**: remote_files.py, cloud_storage.py

### Analysis Tools (`tools/analysis/`)
- **Future**: code_analysis.py, data_analysis.py, log_analysis.py

## 📋 Migration Checklist

### From cursor-db-mcp
- [ ] Extract `CursorDBManager` → `tools/database/cursor_db.py`
- [ ] Move database tools (query_table, refresh_databases, add_project_directory)
- [ ] Migrate resources (list_all_projects, get_project_chat_data, etc.)
- [ ] Transfer prompts (explore_cursor_projects, analyze_chat_data)
- [ ] Fix missing `setup_logging` import
- [ ] Update dependencies and configuration

### From local-file-ingest
- [ ] Implement missing server functionality
- [ ] Create file system tools in `tools/filesystem/local_files.py`
- [ ] Add secure path validation
- [ ] Implement directory traversal protection

## 🔒 Security & Best Practices

### Security Measures
- **Input Validation**: Sanitize all file paths and database queries
- **Path Traversal Protection**: Validate file access within allowed directories
- **Environment Variables**: Never hard-code secrets
- **Error Handling**: Specific exception catching with context
- **Transport Security**: Proper stdio/SSE transport configuration

### Code Quality Standards
- **Type Hints**: Mandatory for all functions and classes
- **Documentation**: Google-style docstrings for classes, NumPy-style for small functions
- **Error Handling**: Catch specific exceptions, re-raise with context
- **Logging**: Use structured logging at INFO level (no print statements)
- **Formatting**: Black formatter with 88-character line length

## 🚀 Implementation Steps

### Step 1: Create Project Structure
```bash
# Navigate to Python source directory
cd ToolRack/Python/src

# Create unified server directory
mkdir -p unified_mcp_server/src/unified_mcp_server/{server,tools,resources,prompts,utils}
mkdir -p unified_mcp_server/src/unified_mcp_server/tools/{database,filesystem}
mkdir -p unified_mcp_server/src/unified_mcp_server/resources/cursor
mkdir -p unified_mcp_server/src/unified_mcp_server/prompts/analysis

# Copy and adapt existing pyproject.toml
cp cursor-db-mcp/pyproject.toml unified_mcp_server/
```

### Step 2: Implement Core Infrastructure
1. Create `server/app.py` with FastMCP setup
2. Implement `server/config.py` with environment configuration
3. Set up `server/logging.py` with proper logging
4. Create `server/lifecycle.py` for app management

### Step 3: Build Tool System
1. Implement `tools/registry.py` for tool discovery
2. Create base classes in `tools/database/base.py` and `tools/filesystem/base.py`
3. Define tool interface contracts and error handling

### Step 4: Migrate Existing Functionality
1. Extract and refactor cursor-db-mcp tools
2. Implement local-file-ingest functionality
3. Update resource and prompt definitions
4. Test migration thoroughly

### Step 5: Testing & Validation
1. Create comprehensive test suite
2. Validate MCP protocol compliance
3. Test transport layers (stdio and SSE)
4. Performance testing with large datasets

## ✅ Success Criteria

- [ ] Single unified MCP server running successfully
- [ ] Clean separation between server infrastructure and tools
- [ ] Tools organized by type with consistent interfaces
- [ ] All existing functionality migrated and working
- [ ] Proper error handling and logging throughout
- [ ] Environment-based configuration
- [ ] Comprehensive documentation
- [ ] Type hints and code quality standards met

## 📚 Dependencies & Tools

### Core Dependencies
- `fastmcp` (>=2.0) - MCP server framework
- `anyio` - Async I/O compatibility
- `pydantic` - Data validation and settings
- `loguru` or `structlog` - Structured logging

### Development Dependencies
- `pytest` - Testing framework
- `black` - Code formatter
- `ruff` - Linter and formatter
- `mypy` - Type checking
- `pre-commit` - Git hooks

## 🔄 Future Enhancements

### Tool Expansion
- Web scraping tools
- API integration tools
- Data processing tools
- Machine learning tools

### Advanced Features
- Tool composition and chaining
- Plugin architecture
- Distributed tool execution
- Real-time monitoring dashboard

---

**Estimated Timeline**: 2-3 weeks for full implementation
**Risk Level**: Medium (dependent on FastMCP API stability)
**Maintenance**: Ongoing (tool additions and updates)