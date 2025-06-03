use std::path::Path;

use rust_mcp_schema::{schema_utils::CallToolError, CallToolResult};
use rust_mcp_sdk::macros::{mcp_tool, JsonSchema};

use crate::fs_service::FileSystemService;

#[mcp_tool(
    name = "read_file",
    description = concat!("Reads the entire content of a single text file and returns it as a string. ",
    "Suitable for examining file contents or loading configuration data. ",
    "IMPORTANT: The path provided MUST be an absolute path (e.g., D:\\my_documents\\report.txt or /home/user/config.json). Relative paths are not supported. ",
    "This operation is restricted to pre-configured allowed directories on the server."),
    destructive_hint = false,
    idempotent_hint = false,
    open_world_hint = false,
    read_only_hint = true
)]
#[derive(::serde::Deserialize, ::serde::Serialize, Clone, Debug, JsonSchema)]
pub struct ReadFileTool {
    /// The **absolute path** of the file to be read (e.g., `D:\\my_documents\\report.txt` or `/home/user/config.json`).
    pub path: String,
}

impl ReadFileTool {
    pub async fn run_tool(
        params: Self,
        context: &FileSystemService,
    ) -> std::result::Result<CallToolResult, CallToolError> {
        let content = context
            .read_file(Path::new(&params.path))
            .await
            .map_err(CallToolError::new)?;

        Ok(CallToolResult::text_content(content, None))
    }
}
