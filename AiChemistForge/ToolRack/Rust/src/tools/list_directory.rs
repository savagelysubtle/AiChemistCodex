use std::path::Path;

use rust_mcp_schema::{schema_utils::CallToolError, CallToolResult};
use rust_mcp_sdk::macros::{mcp_tool, JsonSchema};

use crate::fs_service::FileSystemService;

#[mcp_tool(
    name = "list_directory",
    description = concat!("Provides a detailed listing of all files and subdirectories directly within a specified directory. ",
    "Results are prefixed with [FILE] or [DIR] to distinguish types. ",
    "Essential for exploring directory contents and identifying specific items. ",
    "IMPORTANT: The path provided MUST be an absolute path (e.g., D:\\archive\\documents or /usr/local/bin). Relative paths are not supported. ",
    "This operation is restricted to pre-configured allowed directories on the server."),
    destructive_hint = false,
    idempotent_hint = false,
    open_world_hint = false,
    read_only_hint = true
)]
#[derive(::serde::Deserialize, ::serde::Serialize, Clone, Debug, JsonSchema)]
pub struct ListDirectoryTool {
    /// The **absolute path** of the directory whose contents are to be listed (e.g., `D:\\archive\\documents` or `/usr/local/bin`).
    pub path: String,
}

impl ListDirectoryTool {
    pub async fn run_tool(
        params: Self,
        context: &FileSystemService,
    ) -> std::result::Result<CallToolResult, CallToolError> {
        let entries = context
            .list_directory(Path::new(&params.path))
            .await
            .map_err(CallToolError::new)?;

        let formatted: Vec<_> = entries
            .iter()
            .map(|entry| {
                format!(
                    "{} {}",
                    if entry.path().is_dir() {
                        "[DIR]"
                    } else {
                        "[FILE]"
                    },
                    entry.file_name().to_str().unwrap_or_default()
                )
            })
            .collect();

        Ok(CallToolResult::text_content(formatted.join("\n"), None))
    }
}
