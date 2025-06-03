use std::path::Path;

use rust_mcp_schema::{schema_utils::CallToolError, CallToolResult};
use rust_mcp_sdk::macros::{mcp_tool, JsonSchema};

use crate::fs_service::FileSystemService;

#[derive(::serde::Deserialize, ::serde::Serialize, Clone, Debug, JsonSchema)]
/// Represents a text replacement operation.
pub struct EditOperation {
    /// Text to search for. For multi-line text, ensure line endings match the target file's predominant style (e.g., LF or CRLF) or normalize before sending. The match must be exact.
    #[serde(rename = "oldText")]
    pub old_text: String,
    #[serde(rename = "newText")]
    /// Text to replace the matched `oldText` with. Line endings should be consistent.
    pub new_text: String,
}

#[mcp_tool(
    name = "edit_file",
    description = concat!("Performs line-based edits on a text file by replacing exact sequences of text. ",
    "Multiple edits can be specified. Returns a git-style diff of the changes. ",
    "Useful for precise modifications to existing files. ",
    "IMPORTANT: The file path provided MUST be an absolute path (e.g., D:\\config\\settings.txt or /etc/app/config.yml). Relative paths are not supported. ",
    "This operation is restricted to pre-configured allowed directories on the server."),
    destructive_hint = false,
    idempotent_hint = false,
    open_world_hint = false,
    read_only_hint = false
)]
#[derive(::serde::Deserialize, ::serde::Serialize, Clone, Debug, JsonSchema)]
pub struct EditFileTool {
    /// The **absolute path** of the file to be edited (e.g., `D:\\config\\settings.txt` or `/etc/app/config.yml`).
    pub path: String,

    /// A list of `EditOperation` objects detailing the changes to apply. Edits are applied sequentially.
    pub edits: Vec<EditOperation>,
    /// If true, previews changes as a git-style diff without writing to the file. If false or omitted, changes are applied directly.
    #[serde(
        rename = "dryRun",
        default,
        skip_serializing_if = "std::option::Option::is_none"
    )]
    pub dry_run: Option<bool>,
}

impl EditFileTool {
    pub async fn run_tool(
        params: Self,
        context: &FileSystemService,
    ) -> std::result::Result<CallToolResult, CallToolError> {
        let diff = context
            .apply_file_edits(Path::new(&params.path), params.edits, params.dry_run, None)
            .await
            .map_err(CallToolError::new)?;

        Ok(CallToolResult::text_content(diff, None))
    }
}
