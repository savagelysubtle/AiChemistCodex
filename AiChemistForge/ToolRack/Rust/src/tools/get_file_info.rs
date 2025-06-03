use std::path::Path;

use rust_mcp_schema::{schema_utils::CallToolError, CallToolResult};
use rust_mcp_sdk::macros::{mcp_tool, JsonSchema};

use crate::fs_service::FileSystemService;

#[mcp_tool(
    name = "get_file_info",
    description = concat!("Retrieves detailed metadata for a specified file or directory. ",
    "Information includes size, creation/modification timestamps, and type (file/directory). ",
    "Useful for checking file existence, size, or type before other operations. ",
    "IMPORTANT: The path provided MUST be an absolute path (e.g., D:\\logs\\app.log or /var/www/html). Relative paths are not supported. ",
    "This operation is restricted to pre-configured allowed directories on the server."),
    destructive_hint = false,
    idempotent_hint = false,
    open_world_hint = false,
    read_only_hint = true
)]
#[derive(::serde::Deserialize, ::serde::Serialize, Clone, Debug, JsonSchema)]
pub struct GetFileInfoTool {
    /// The **absolute path** to the file or directory for which to retrieve information (e.g., `D:\\logs\\app.log` or `/var/www/html`).
    pub path: String,
}

impl GetFileInfoTool {
    pub async fn run_tool(
        params: Self,
        context: &FileSystemService,
    ) -> std::result::Result<CallToolResult, CallToolError> {
        let stats = context
            .get_file_stats(Path::new(&params.path))
            .await
            .map_err(CallToolError::new)?;
        Ok(CallToolResult::text_content(stats.to_string(), None))
    }
}
