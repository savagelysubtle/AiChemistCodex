use rust_mcp_schema::{schema_utils::CallToolError, CallToolResult};
use rust_mcp_sdk::macros::{mcp_tool, JsonSchema};

use crate::fs_service::FileSystemService;

#[mcp_tool(
    name = "list_allowed_directories",
    description = concat!("Returns a list of the absolute base directory paths that this MCP server instance is permitted to access. ",
    "Operations are confined to these directories and their subdirectories. ",
    "Use this tool to understand the server's operational scope before attempting file operations. ",
    "No parameters are required for this tool."),
    destructive_hint = false,
    idempotent_hint = false,
    open_world_hint = false,
    read_only_hint = true
)]
#[derive(::serde::Deserialize, ::serde::Serialize, Clone, Debug, JsonSchema)]
pub struct ListAllowedDirectoriesTool {}

impl ListAllowedDirectoriesTool {
    pub async fn run_tool(
        _: Self,
        context: &FileSystemService,
    ) -> std::result::Result<CallToolResult, CallToolError> {
        let result = format!(
            "Allowed directories:\n{}",
            context
                .allowed_directories()
                .iter()
                .map(|entry| entry.display().to_string())
                .collect::<Vec<_>>()
                .join("\n")
        );
        Ok(CallToolResult::text_content(result, None))
    }
}
