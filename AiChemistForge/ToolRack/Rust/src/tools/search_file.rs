use std::path::Path;

use rust_mcp_schema::{schema_utils::CallToolError, CallToolResult};
use rust_mcp_sdk::macros::{mcp_tool, JsonSchema};

use crate::fs_service::FileSystemService;
#[mcp_tool(
    name = "search_files",
    description = concat!("Recursively searches for files and directories matching a glob pattern within a specified starting directory. ",
    "The search is case-insensitive and matches partial names if the pattern allows. Returns a list of full absolute paths for all matches. ",
    "Useful for finding items when their exact location or full name is unknown. Supports exclude patterns. ",
    "IMPORTANT: The starting path provided MUST be an absolute path (e.g., D:\\projects or /var/log). Relative paths are not supported. ",
    "This operation is restricted to pre-configured allowed directories on the server."),
    destructive_hint = false,
    idempotent_hint = false,
    open_world_hint = false,
    read_only_hint = true
)]
#[derive(::serde::Deserialize, ::serde::Serialize, Clone, Debug, JsonSchema)]

/// A tool for searching files based on a path and pattern.
pub struct SearchFilesTool {
    /// The **absolute directory path** from which to start the search (e.g., `D:\\projects` or `/var/log`).
    pub path: String,
    /// The glob pattern to match against file/directory names (e.g., `*.txt`, `my_app*`, `**/*config*.json`). Case-insensitive.
    pub pattern: String,
    #[serde(rename = "excludePatterns")]
    /// Optional list of glob patterns to exclude from search results (e.g., `["*.tmp", "**/cache/**"]`).
    pub exclude_patterns: Option<Vec<String>>,
}
impl SearchFilesTool {
    pub async fn run_tool(
        params: Self,
        context: &FileSystemService,
    ) -> std::result::Result<CallToolResult, CallToolError> {
        let list = context
            .search_files(
                Path::new(&params.path),
                params.pattern,
                params.exclude_patterns.unwrap_or_default(),
            )
            .map_err(CallToolError::new)?;

        let result = if !list.is_empty() {
            list.iter()
                .map(|entry| entry.path().display().to_string())
                .collect::<Vec<_>>()
                .join("\n")
        } else {
            "No matches found".to_string()
        };
        Ok(CallToolResult::text_content(result, None))
    }
}
