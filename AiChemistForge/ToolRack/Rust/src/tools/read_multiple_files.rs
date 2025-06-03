use std::path::Path;

use futures::future::join_all;
use rust_mcp_schema::{schema_utils::CallToolError, CallToolResult};
use rust_mcp_sdk::macros::{mcp_tool, JsonSchema};

use crate::fs_service::FileSystemService;

#[mcp_tool(
    name = "read_multiple_files",
    description = concat!("Reads the content of multiple text files simultaneously and returns them as a single string, with each file's content clearly demarcated. ",
    "More efficient than reading files individually when multiple files are needed. ",
    "If a file cannot be read, an error message for that specific file is included in the output; other files are still processed. ",
    "IMPORTANT: All paths in the list MUST be absolute paths (e.g., D:\\sources\\file1.rs or /opt/app/data.csv). Relative paths are not supported. ",
    "This operation is restricted to pre-configured allowed directories on the server."),
    destructive_hint = false,
    idempotent_hint = false,
    open_world_hint = false,
    read_only_hint = true
)]
#[derive(::serde::Deserialize, ::serde::Serialize, Clone, Debug, JsonSchema)]
pub struct ReadMultipleFilesTool {
    /// A list of **absolute file paths** to be read (e.g., `["D:\\sources\\file1.rs", "D:\\sources\\file2.java"]`).
    pub paths: Vec<String>,
}

impl ReadMultipleFilesTool {
    pub async fn run_tool(
        params: Self,
        context: &FileSystemService,
    ) -> std::result::Result<CallToolResult, CallToolError> {
        let content_futures: Vec<_> = params
            .paths
            .iter()
            .map(|path| async move {
                {
                    let content = context
                        .read_file(Path::new(&path))
                        .await
                        .map_err(CallToolError::new);

                    content.map_or_else(
                        |err| format!("{}: Error - {}", path, err),
                        |value| format!("{}:\n{}\n", path, value),
                    )
                }
            })
            .collect();

        let contents = join_all(content_futures).await;

        Ok(CallToolResult::text_content(contents.join("\n---\n"), None))
    }
}
