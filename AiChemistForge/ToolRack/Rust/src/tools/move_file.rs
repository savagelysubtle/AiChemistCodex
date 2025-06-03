use std::path::Path;

use rust_mcp_schema::{schema_utils::CallToolError, CallToolResult};
use rust_mcp_sdk::macros::{mcp_tool, JsonSchema};

use crate::fs_service::FileSystemService;

#[mcp_tool(
    name = "move_file",
    description = concat!("Moves or renames a file or directory. ",
    "Can move items between directories or rename them within the same directory. The destination path must not already exist. ",
    "IMPORTANT: Both source and destination paths MUST be absolute paths (e.g., D:\\old_folder\\item.dat or /tmp/file_to_move). Relative paths are not supported. ",
    "This operation is restricted to pre-configured allowed directories on the server."),
    destructive_hint = false,
    idempotent_hint = false,
    open_world_hint = false,
    read_only_hint = false
)]
#[derive(::serde::Deserialize, ::serde::Serialize, Clone, Debug, JsonSchema)]
pub struct MoveFileTool {
    /// The **absolute source path** of the file or directory to be moved/renamed (e.g., `D:\\old_folder\\item.dat`).
    pub source: String,
    /// The **absolute destination path** for the file or directory (e.g., `D:\\new_location\\item_new_name.dat`). This path must not already exist.
    pub destination: String,
}

impl MoveFileTool {
    pub async fn run_tool(
        params: Self,
        context: &FileSystemService,
    ) -> std::result::Result<CallToolResult, CallToolError> {
        context
            .move_file(Path::new(&params.source), Path::new(&params.destination))
            .await
            .map_err(CallToolError::new)?;

        Ok(CallToolResult::text_content(
            format!(
                "Successfully moved {} to {}",
                &params.source, &params.destination
            ),
            None,
        ))
    }
}
