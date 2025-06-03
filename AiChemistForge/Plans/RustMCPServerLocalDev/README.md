# Plan: Local Development Setup for Rust MCP Filesystem Server

**Objective**: Enable local development of the Rust MCP filesystem server to facilitate improvements, particularly to tool descriptions. This involves running the server directly from source using `cargo` and configuring a local MCP client to connect to this development instance.

**Phases & Steps**:

**Phase 1: Preparation & Understanding (Partially Complete)**

1.  **Review Project Structure (Done)**:
    *   Familiarized with `main.rs`, `cli.rs`, `server.rs`, `handler.rs`, `tools.rs`, and `Cargo.toml`.
2.  **Identify Tool Definition Mechanism (Partially Done)**:
    *   The `tool_box!` macro in `src/tools.rs` is key.
    *   Individual tool logic is in modules like `src/tools/read_files.rs` (and others in `src/tools/`).
    *   **Next Step**: Inspect the contents of the `src/tools/` directory and a few sample tool modules (e.g., `read_files.rs`, `write_file.rs`) to see exactly how descriptions are specified (likely via struct/enum attributes or comments that the `tool_box!` macro processes).

**Phase 2: Local Server Execution**

1.  **Determine `cargo run` Command**:
    *   Based on `src/cli.rs`, the command will be `cargo run -- --allow-write <allowed_directory_1> <allowed_directory_2> ...`.
    *   For example: `cargo run -- --allow-write D:\test_mcp_dir1 F:\test_mcp_dir2`
    *   The `--` is important to separate `cargo run` arguments from the application\'s arguments.
2.  **Initial Local Test Run**:
    *   Open a terminal in the `D:/Coding/AiChemistCodex/AiChemistForge/ToolRack/Rust/` directory.
    *   Execute the `cargo run` command with appropriate example directories (you\'ll need to create these test directories if they don\'t exist).
    *   Verify the server starts and prints its startup message (seen in `MyServerHandler::startup_message`).

**Phase 3: Local `mcp.json` Configuration**

1.  **Create `mcp.local.json`**:
    *   Create a new file named `mcp.local.json` (or similar, to distinguish from the global one) in a suitable location. For instance, you could place it in `D:/Coding/AiChemistCodex/AiChemistForge/.cursor/mcp.local.json` or `D:/Coding/AiChemistCodex/AiChemistForge/ToolRack/Rust/mcp.local.json`.
2.  **Define Server Configuration**:
    *   The configuration will be similar to your existing `mcp.json` but will use `cargo` for the command.
    *   **Example `mcp.local.json` content**:
        ```json
        {
          "mcpServers": {
            "filesystem-local-dev": { // Unique name for the local server
              "command": "cargo",
              "args": [
                "run",
                "--manifest-path",
                "D:/Coding/AiChemistCodex/AiChemistForge/ToolRack/Rust/Cargo.toml", // Ensure cargo runs in the correct project
                "--", // Separator for application arguments
                "--allow-write",
                "D:/Coding/AiChemistCodex/AiChemistForge/temp/mcp_allowed_dir1", // Example allowed directory
                "D:/Coding/AiChemistCodex/AiChemistForge/temp/mcp_allowed_dir2"  // Example allowed directory
                // Add other allowed directories as needed
              ],
              "cwd": "D:/Coding/AiChemistCodex/AiChemistForge/ToolRack/Rust/", // Working directory for the cargo command
              "env": {
                "RUST_LOG": "debug" // Optional: for more detailed logging from the Rust app
              }
            }
          }
        }
        ```
    *   **Important**:
        *   You\'ll need to adjust the `allowed_directories` paths to actual directories you want to use for testing. Create them if they don\'t exist. Using a `temp` subfolder in your project is a good practice.
        *   The `cwd` (current working directory) should be the root of your Rust project so `cargo run` works correctly.
        *   The `--manifest-path` argument explicitly tells `cargo` where to find the `Cargo.toml` file for the project.
3.  **Configure MCP Client**:
    *   Update your MCP client (e.g., Claude for Desktop, or whatever system consumes `mcp.json`) to load this `mcp.local.json` file. This step is client-specific.

**Phase 4: Modifying Tool Descriptions**

1.  **Locate Tool Description Source**:
    *   Based on the upcoming inspection of `src/tools/` and its submodules, pinpoint where tool descriptions are defined (e.g., as `#[doc = "..."]` attributes on tool structs, or another mechanism used by `tool_box!`).
2.  **Modify Descriptions**:
    *   Edit the Rust source files to update the descriptions.
3.  **Recompile and Test**:
    *   After changes, the `cargo run` command will automatically recompile.
    *   Use your MCP client (now pointing to the local server) to list tools and verify the updated descriptions appear.

**Next Steps for User (Steve)**:
*   Review this plan.
*   Create the test directories (e.g., `D:/Coding/AiChemistCodex/AiChemistForge/temp/mcp_allowed_dir1`) if they don\'t already exist.
*   Perform the "Initial Local Test Run" (Phase 2, Step 2).
*   Create the `mcp.local.json` file (Phase 3, Step 1 & 2) in `D:/Coding/AiChemistCodex/AiChemistForge/.cursor/mcp.local.json` (or your preferred location for client configuration).
*   Configure your MCP client to use this new local configuration.
