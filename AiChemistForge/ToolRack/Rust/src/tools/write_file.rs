use rust_mcp_sdk::macros::{mcp_tool, JsonSchema};
use std::path::Path;

use rust_mcp_schema::{schema_utils::CallToolError, CallToolResult};

use crate::fs_service::FileSystemService;
#[mcp_tool(
    name = "write_file",
    description = concat!("Writes new content to a file, creating the file if it doesn't exist or completely overwriting it if it does. ",
    "Use with caution, as existing file content will be lost. Handles text content with UTF-8 encoding. ",
    "IMPORTANT: The path provided MUST be an absolute path (e.g., D:\\output\\result.json or /app/data/new_file.txt). Relative paths are not supported. ",
    "This operation is restricted to pre-configured allowed directories on the server."),
    destructive_hint = false,
    idempotent_hint = false,
    open_world_hint = false,
    read_only_hint = false
)]
#[derive(Debug, Clone, ::serde::Deserialize, ::serde::Serialize, JsonSchema)]
pub struct WriteFileTool {
    /// The **absolute path** of the file to be written to (e.g., `D:\\output\\result.json` or `/app/data/new_file.txt`).
    pub path: String,
    /// The string content to be written to the file.
    pub content: String,
}

impl WriteFileTool {
    pub async fn run_tool(
        params: Self,
        context: &FileSystemService,
    ) -> std::result::Result<CallToolResult, CallToolError> {
        context
            .write_file(Path::new(&params.path), &params.content)
            .await
            .map_err(CallToolError::new)?;

        Ok(CallToolResult::text_content(
            format!("Successfully wrote to {}", &params.path),
            None,
        ))
    }
}
