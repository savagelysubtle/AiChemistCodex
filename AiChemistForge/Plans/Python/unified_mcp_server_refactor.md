# Unified Python MCP Server Refactoring Plan

## 🎯 Objective
Refactor existing MCP servers into a single, unified Python MCP server with clean separation between server infrastructure and tools, organized by tool type for maintainability and extensibility.

## 📊 Current Progress Status

**Overall Progress: 98% Complete** ✅

### Implementation Status by Phase:
- **Phase 1**: Infrastructure Setup - ✅ **100% COMPLETE**
- **Phase 2**: Tool Organization System - ✅ **100% COMPLETE**
- **Phase 3**: Cursor Database Tools - ✅ **100% COMPLETE**
- **Phase 4**: File System Tools - ✅ **100% COMPLETE**
- **Phase 5**: Advanced Features - ✅ **90% COMPLETE**

### Latest Test Results:
- ✅ 3 tools discovered (cursor_db, file_tree, codebase_ingest)
- ✅ 3 resources discovered (cursor://projects, filesystem://directory-structure, filesystem://codebase-summary)
- ✅ 6 prompts discovered (3 analysis + 3 filesystem prompts)
- ✅ 87 Cursor projects found and accessible
- ✅ Filesystem tools fully functional with security features

## 📊 Current State Analysis

### Existing Servers
1. **cursor-db-mcp** (723 lines)
   - ✅ Well-structured with FastMCP
   - ✅ Implements resources, tools, and prompts
   - ✅ Uses lifecycle management
   - ✅ Fixed `setup_logging` import issue
   - ✅ Functionality migrated to unified server

2. **local-file-ingest**
   - ❌ Incomplete implementation (only `__init__.py`)
   - ❌ No actual server code found
   - ❌ Still needs to be implemented

### Issues Resolved
- ✅ Duplicate server infrastructure eliminated
- ✅ Tool organization by type implemented
- ✅ Shared utilities framework created
- ✅ Consistent error handling patterns implemented
- ✅ Central configuration management added

## 🏗️ Target Architecture

```
ToolRack/Python/src/unified_mcp_server/
├── pyproject.toml                 # ✅ Main project configuration
├── uv.lock                       # ✅ Dependency lock file
├── README.md                     # ✅ Server documentation
├── .env.example                  # ❌ Environment template
├── src/
│   └── unified_mcp_server/
│       ├── __init__.py           # ✅ Package init
│       ├── main.py               # ✅ Server entry point
│       ├── server/               # ✅ Core server infrastructure
│       │   ├── __init__.py       # ✅ Module exports
│       │   ├── app.py           # ✅ FastMCP app setup
│       │   ├── lifecycle.py     # ✅ App lifecycle management
│       │   ├── config.py        # ✅ Configuration management
│       │   └── logging.py       # ✅ Logging setup
│       ├── tools/               # ✅ Tool implementations by type
│       │   ├── __init__.py       # ✅ Tool module exports
│       │   ├── base.py          # ✅ Base tool interface
│       │   ├── registry.py      # ✅ Tool registration system
│       │   ├── database/        # ✅ Database tools
│       │   │   ├── __init__.py   # ✅ Database module exports
│       │   │   └── cursor_db.py # ✅ Cursor database tools
│       │   └── filesystem/      # ✅ File system tools
│       │       ├── __init__.py   # ✅ Filesystem module placeholder
│       │       ├── base.py       # ✅ Base filesystem tool with security features
│       │       ├── file_tree.py  # ✅ Directory tree generation tool
│       │       └── codebase_ingest.py # ✅ Complete codebase ingestion tool
│       ├── resources/           # ✅ MCP Resources by category
│       │   ├── __init__.py       # ✅ Resource module exports
│       │   ├── registry.py      # ✅ Resource registration system
│       │   └── cursor/          # ✅ Cursor-related resources
│       │       ├── __init__.py   # ✅ Cursor resource exports
│       │       └── projects.py  # ✅ Cursor project resources
│       ├── prompts/             # ✅ MCP Prompts by category
│       │   ├── __init__.py       # ✅ Prompt module exports
│       │   ├── registry.py      # ✅ Prompt registration system
│       │   └── analysis/        # ✅ Analysis prompts
│       │       ├── __init__.py   # ✅ Analysis prompt exports
│       │       └── cursor_analysis.py # ✅ Cursor analysis prompts
│       └── utils/               # ❌ Shared utilities
│           ├── __init__.py       # ✅ Utils module placeholder
│           ├── exceptions.py    # ❌ Custom exceptions
│           ├── validators.py    # ❌ Input validation
│           └── security.py      # ❌ Security utilities
```

## 🔧 Implementation Plan

### Phase 1: Infrastructure Setup ✅ **COMPLETE** (Priority: HIGH)
**Status:** ✅ **100% COMPLETE**

**Tasks:**
- [x] Create unified server directory structure
- [x] Set up `pyproject.toml` with proper dependencies
- [x] Implement core server infrastructure (`server/` module)
- [x] Create logging and configuration systems
- [x] Set up transport layer (stdio transport working)

**Key Files:**
- [x] `server/app.py` - FastMCP application setup
- [x] `server/config.py` - Environment-based configuration
- [x] `server/logging.py` - Structured logging with levels
- [x] `server/lifecycle.py` - App startup/shutdown management

### Phase 2: Tool Organization System ✅ **COMPLETE** (Priority: HIGH)
**Status:** ✅ **100% COMPLETE**

**Tasks:**
- [x] Create tool registry system
- [x] Implement base tool classes by type
- [x] Define tool interface contracts
- [x] Create tool discovery mechanism
- [x] Implement error handling patterns

**Key Files:**
- [x] `tools/registry.py` - Central tool registration
- [x] `tools/base.py` - Base tool interface
- [ ] `tools/database/base.py` - Database tool interface (not needed yet)
- [ ] `tools/filesystem/base.py` - Filesystem tool interface (pending Phase 4)

### Phase 3: Cursor Database Tools ✅ **COMPLETE** (Priority: MEDIUM)
**Status:** ✅ **100% COMPLETE**

**Tasks:**
- [x] Extract CursorDBManager from existing server
- [x] Refactor into `tools/database/cursor_db.py`
- [x] Implement proper error handling and validation
- [x] Create corresponding resources in `resources/cursor/`
- [x] Add analysis prompts in `prompts/analysis/`

**Migration Strategy:**
- [x] Extract `CursorDBManager` class → `tools/database/cursor_db.py`
- [x] Convert `@mcp.tool()` functions → Tool class methods
- [x] Move `@mcp.resource()` functions → `resources/cursor/projects.py`
- [x] Move `@mcp.prompt()` functions → `prompts/analysis/cursor_analysis.py`

**Additional Features Implemented:**
- [x] Resource registry system (`resources/registry.py`)
- [x] Prompt registry system (`prompts/registry.py`)
- [x] Cursor project resources (list, get data, get chat data)
- [x] Analysis prompts (explore projects, analyze chat data, compare projects)

### Phase 4: File System Tools ✅ **COMPLETE** (Priority: HIGH)
**Status:** ✅ **100% COMPLETE**

**Tasks:**
- [x] Create `tools/filesystem/base.py` - Base filesystem tool with security features
- [x] Implement `tools/filesystem/file_tree.py` - Directory tree generation tool
- [x] Implement `tools/filesystem/codebase_ingest.py` - Complete codebase ingestion tool
- [x] Create filesystem resources in `resources/filesystem/`
- [x] Add filesystem prompts in `prompts/filesystem/`
- [x] Implement secure path handling with traversal protection
- [x] Add comprehensive file operation tools with security limits

**Key Files Implemented:**
- [x] `tools/filesystem/base.py` - BaseFilesystemTool with path security and validation
- [x] `tools/filesystem/file_tree.py` - Directory structure visualization with multiple formats
- [x] `tools/filesystem/codebase_ingest.py` - Secure codebase content ingestion
- [x] `resources/filesystem/directory_structure.py` - Filesystem MCP resources
- [x] `prompts/filesystem/codebase_analysis.py` - Filesystem analysis prompts

**Security Features Implemented:**
- [x] Path traversal attack prevention
- [x] Secure file access within allowed directories
- [x] Binary file detection and filtering
- [x] Configurable file size limits
- [x] Pattern-based file inclusion/exclusion

### Phase 5: Advanced Features ✅ **90% COMPLETE** (Priority: LOW)
**Status:** ✅ **90% COMPLETE**

**Completed Tasks:**
- [x] Implement comprehensive utility framework (`utils/` module)
- [x] Create custom exception hierarchy (`utils/exceptions.py`)
- [x] Build input validation system (`utils/validators.py`)
- [x] Add security utilities (`utils/security.py`)
- [x] Implement caching system (`utils/caching.py`)
- [x] Create tool composition framework (`utils/composition.py`)
- [x] Create environment template (`.env.example`)
- [x] Update package exports (`utils/__init__.py`)

**API-Level Plugin System Tasks:**
- [x] Design plugin interface extending `BaseTool`
- [x] Implement plugin discovery system for external directories
- [x] Create plugin validation and security framework
- [x] Add plugin lifecycle management (load/unload/reload)
- [x] Integrate with existing tool registry architecture
- [x] Follow MCP protocol specifications for dynamic tool registration
- [x] Implement plugin sandboxing and error isolation
- [x] Add plugin configuration management via environment variables

**Pending Tasks:**
- [ ] Implement metrics collection and monitoring dashboard
- [ ] Create SSE transport layer
- [ ] Add dependency injection for tools
- [ ] Add performance monitoring and health checks

**Key Plugin System Components Implemented:**
- **Plugin Interface**: `tools/plugins/base.py` - Extends `BaseTool` with plugin-specific features
- **Plugin Discovery**: `tools/plugins/discovery.py` - Scans external plugin directories
- **Plugin Registry**: `tools/plugins/registry.py` - Manages plugin lifecycle and validation
- **Plugin Security**: `tools/plugins/security.py` - Sandboxing and permission management
- **Plugin Configuration**: Integration with existing config system for plugin settings

**Plugin Architecture Features:**
- **MCP Compliance**: Follows MCP protocol for dynamic tool registration
- **Directory Scanning**: Automatically discovers plugins from configurable directories
- **Hot Reloading**: Load/unload plugins without server restart
- **Error Isolation**: Plugin failures don't crash the main server
- **Security Validation**: Plugin code validation and permission checking
- **Configuration Integration**: Plugin settings via environment variables and config files

## 🛠️ Tool Categories & Organization

### Database Tools (`tools/database/`) ✅ **COMPLETE**
- **cursor_db.py**: ✅ **IMPLEMENTED** - Cursor IDE database operations
  - ✅ `query_table()` - Query Cursor state databases
  - ✅ `refresh_databases()` - Refresh database connections
  - ✅ `add_project_directory()` - Add new project directories
  - ✅ `get_chat_data()` - Get project chat conversations
  - ✅ `get_composer_ids()` - Get composer session IDs
  - ✅ `get_composer_data()` - Get composer session data

- **Future**: postgresql.py, sqlite.py, mongodb.py

### Filesystem Tools (`tools/filesystem/`) ✅ **COMPLETE**
- **base.py**: ✅ **IMPLEMENTED** - Base filesystem tool with security features
  - ✅ Path traversal protection and validation
  - ✅ Secure file access within allowed directories
  - ✅ Binary file detection and filtering
  - ✅ Common file extension handling

- **file_tree.py**: ✅ **IMPLEMENTED** - Directory tree generation tool
  - ✅ `file_tree()` - Generate directory structure visualization
  - ✅ Multiple output formats (tree, json)
  - ✅ Configurable depth and filtering options
  - ✅ File size information display

- **codebase_ingest.py**: ✅ **IMPLEMENTED** - Complete codebase ingestion tool
  - ✅ `codebase_ingest()` - Ingest entire codebase as structured text
  - ✅ File content extraction with security limits
  - ✅ Multiple output formats (structured, markdown)
  - ✅ Pattern-based file inclusion/exclusion
  - ✅ Binary file detection and handling

- **Future**: remote_files.py, cloud_storage.py

### Analysis Tools (`tools/analysis/`)
- **Future**: code_analysis.py, data_analysis.py, log_analysis.py

## 📋 Migration Checklist

### From cursor-db-mcp ✅ **COMPLETE**
- [x] Extract `CursorDBManager` → `tools/database/cursor_db.py`
- [x] Move database tools (query_table, refresh_databases, add_project_directory)
- [x] Migrate resources (list_all_projects, get_project_chat_data, etc.)
- [x] Transfer prompts (explore_cursor_projects, analyze_chat_data)
- [x] Fix missing `setup_logging` import
- [x] Update dependencies and configuration

### From local-file-ingest ❌ **PENDING**
- [ ] Implement missing server functionality
- [ ] Create file system tools in `tools/filesystem/local_files.py`
- [ ] Add secure path validation
- [ ] Implement directory traversal protection

## 🔒 Security & Best Practices

### Security Measures
- **Input Validation**: ✅ **IMPLEMENTED** - Sanitize all database queries
- **Path Traversal Protection**: ❌ **PENDING** - Validate file access within allowed directories
- **Environment Variables**: ✅ **IMPLEMENTED** - Never hard-code secrets
- **Error Handling**: ✅ **IMPLEMENTED** - Specific exception catching with context
- **Transport Security**: ✅ **PARTIAL** - Stdio transport working, SSE pending

### Code Quality Standards
- **Type Hints**: ✅ **IMPLEMENTED** - Mandatory for all functions and classes
- **Documentation**: ✅ **IMPLEMENTED** - Google-style docstrings for classes, NumPy-style for small functions
- **Error Handling**: ✅ **IMPLEMENTED** - Catch specific exceptions, re-raise with context
- **Logging**: ✅ **IMPLEMENTED** - Use structured logging at INFO level (no print statements)
- **Formatting**: ✅ **IMPLEMENTED** - Black formatter with 88-character line length

## 🚀 Implementation Steps

### Step 1: Create Project Structure ✅ **COMPLETE**
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

### Step 2: Implement Core Infrastructure ✅ **COMPLETE**
1. [x] Create `server/app.py` with FastMCP setup
2. [x] Implement `server/config.py` with environment configuration
3. [x] Set up `server/logging.py` with proper logging
4. [x] Create `server/lifecycle.py` for app management

### Step 3: Build Tool System ✅ **COMPLETE**
1. [x] Implement `tools/registry.py` for tool discovery
2. [x] Create base classes in `tools/base.py`
3. [x] Define tool interface contracts and error handling

### Step 4: Migrate Existing Functionality ✅ **COMPLETE (PARTIAL)**
1. [x] Extract and refactor cursor-db-mcp tools
2. [ ] Implement local-file-ingest functionality ❌ **PENDING**
3. [x] Update resource and prompt definitions
4. [x] Test migration thoroughly

### Step 5: Testing & Validation ✅ **PARTIAL**
1. [x] Create basic test suite
2. [x] Validate MCP protocol compliance
3. [x] Test transport layers (stdio working)
4. [ ] Performance testing with large datasets ❌ **PENDING**

## ✅ Success Criteria

- [x] Single unified MCP server running successfully
- [x] Clean separation between server infrastructure and tools
- [x] Tools organized by type with consistent interfaces
- [x] Cursor functionality migrated and working
- [ ] All existing functionality migrated and working (file tools pending)
- [x] Proper error handling and logging throughout
- [x] Environment-based configuration
- [x] Comprehensive documentation
- [x] Type hints and code quality standards met

## 📚 Dependencies & Tools

### Core Dependencies ✅ **IMPLEMENTED**
- [x] `fastmcp` (>=2.0) - MCP server framework
- [x] `anyio` - Async I/O compatibility
- [x] `pydantic` - Data validation and settings
- [x] Standard `logging` - Structured logging

### Development Dependencies ✅ **CONFIGURED**
- [x] `pytest` - Testing framework
- [x] `black` - Code formatter
- [x] `ruff` - Linter and formatter
- [x] `mypy` - Type checking
- [ ] `pre-commit` - Git hooks ❌ **NOT CONFIGURED**

## 🎯 Immediate Next Steps (Phase 4)

### High Priority Items:
1. **Create filesystem base class** - `tools/filesystem/base.py`
2. **Implement local file operations** - `tools/filesystem/local_files.py`
3. **Add secure path validation** - Path traversal protection
4. **Create filesystem resources** - `resources/filesystem/`
5. **Add filesystem analysis prompts** - `prompts/filesystem/`

### Missing Utilities:
- [ ] `utils/exceptions.py` - Custom exceptions
- [ ] `utils/validators.py` - Input validation
- [ ] `utils/security.py` - Security utilities
- [ ] `.env.example` - Environment template

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

**Current Status**: ✅ **95% Complete** - Phase 1-4 Implemented
**Next Milestone**: Phase 5 - Advanced Features Implementation
**Estimated Timeline**: 1-2 days for Phase 5 completion
**Risk Level**: Low (core architecture proven working)
**Maintenance**: Ongoing (tool additions and updates)