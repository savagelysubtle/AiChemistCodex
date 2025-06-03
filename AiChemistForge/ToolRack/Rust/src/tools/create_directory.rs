use std::path::Path;

use rust_mcp_schema::{schema_utils::CallToolError, CallToolResult};
use rust_mcp_sdk::macros::{mcp_tool, JsonSchema};

use crate::fs_service::FileSystemService;

#[mcp_tool(
    name = "create_directory",
    description = concat!("Creates a new directory, including any necessary parent directories if they do not exist. ",
    "If the directory already exists, the operation completes successfully without error. ",
    "This tool is ideal for preparing directory structures for new projects or ensuring output paths are available. ",
    "IMPORTANT: The path provided MUST be an absolute path (e.g., D:\\projects\\new_folder or /mnt/data/new_folder). Relative paths are not supported. ",
    "This operation is restricted to pre-configured allowed directories on the server."),
    destructive_hint = false,
    idempotent_hint = false,
    open_world_hint = false,
    read_only_hint = false
)]
#[derive(::serde::Deserialize, ::serde::Serialize, Clone, Debug, JsonSchema)]
pub struct CreateDirectoryTool {
    /// The **absolute path** where the directory will be created (e.g., `D:\\projects\\new_folder` or `/mnt/data/new_folder`).
    pub path: String,
}

impl CreateDirectoryTool {
    pub async fn run_tool(
        params: Self,
        context: &FileSystemService,
    ) -> std::result::Result<CallToolResult, CallToolError> {
        context
            .create_directory(Path::new(&params.path))
            .await
            .map_err(CallToolError::new)?;

        Ok(CallToolResult::text_content(
            format!("Successfully created directory {}", &params.path),
            None,
        ))
    }
}
