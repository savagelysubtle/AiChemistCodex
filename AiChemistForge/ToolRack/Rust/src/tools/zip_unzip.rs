use rust_mcp_schema::{schema_utils::CallToolError, CallToolResult};
use rust_mcp_sdk::macros::{mcp_tool, JsonSchema};

use crate::fs_service::FileSystemService;

#[mcp_tool(
    name = "zip_files",
    description = concat!("Creates a ZIP archive from a list of specified input files. ",
    "The resulting ZIP file is saved to the `target_zip_file` path. ",
    "IMPORTANT: All file paths in `input_files` and the `target_zip_file` path MUST be absolute paths. Relative paths are not supported. ",
    "Both source files and the target ZIP file location must be within pre-configured allowed directories on the server."),
    destructive_hint = false,
    idempotent_hint = false,
    open_world_hint = false,
    read_only_hint = false
)]
#[derive(::serde::Deserialize, ::serde::Serialize, Clone, Debug, JsonSchema)]
pub struct ZipFilesTool {
    /// A list of **absolute paths** to the files that should be included in the ZIP archive.
    pub input_files: Vec<String>,
    /// The **absolute path** (including filename and .zip extension) where the generated ZIP archive will be saved.
    pub target_zip_file: String,
}

impl ZipFilesTool {
    pub async fn run_tool(
        params: Self,
        context: &FileSystemService,
    ) -> std::result::Result<CallToolResult, CallToolError> {
        let result_content = context
            .zip_files(params.input_files, params.target_zip_file)
            .await
            .map_err(CallToolError::new)?;
        //TODO: return resource?
        Ok(CallToolResult::text_content(result_content, None))
    }
}

#[mcp_tool(
    name = "unzip_file",
    description = concat!("Extracts all contents of a ZIP archive to a specified target directory. ",
    "The directory structure within the ZIP file is recreated at the target location. ",
    "IMPORTANT: The `zip_file` path and the `target_path` MUST be absolute paths. Relative paths are not supported. ",
    "Both the source ZIP file and the target extraction directory must be within pre-configured allowed directories on the server.")
)]
#[derive(::serde::Deserialize, ::serde::Serialize, Clone, Debug, JsonSchema)]
pub struct UnzipFileTool {
    /// The **absolute path** to the existing ZIP file that needs to be extracted.
    pub zip_file: String,
    /// The **absolute path** to the target directory where the contents of the ZIP file will be extracted. This directory will be created if it doesn't exist.
    pub target_path: String,
}

impl UnzipFileTool {
    pub async fn run_tool(
        params: Self,
        context: &FileSystemService,
    ) -> std::result::Result<CallToolResult, CallToolError> {
        let result_content = context
            .unzip_file(&params.zip_file, &params.target_path)
            .await
            .map_err(CallToolError::new)?;
        //TODO: return resource?
        Ok(CallToolResult::text_content(result_content, None))
    }
}

#[mcp_tool(
    name = "zip_directory",
    description = concat!("Creates a ZIP archive from the contents of an entire directory, optionally filtering by a glob pattern. ",
    "Includes files and subdirectories. The resulting ZIP file is saved to `target_zip_file`. ",
    "IMPORTANT: The `input_directory` and `target_zip_file` paths MUST be absolute paths. Relative paths are not supported. ",
    "Both the source directory and the target ZIP file location must be within pre-configured allowed directories on the server.")
)]
#[derive(::serde::Deserialize, ::serde::Serialize, Clone, Debug, JsonSchema)]
pub struct ZipDirectoryTool {
    /// The **absolute path** to the directory whose contents will be zipped.
    pub input_directory: String,
    /// An optional glob pattern (e.g., `*.log`, `**/*.txt`) to filter which files and subdirectories are included. Defaults to `**/*` (all contents) if omitted or null.
    pub pattern: Option<String>,
    /// The **absolute path** (including filename and .zip extension) where the generated ZIP archive will be saved.
    pub target_zip_file: String,
}

impl ZipDirectoryTool {
    pub async fn run_tool(
        params: Self,
        context: &FileSystemService,
    ) -> std::result::Result<CallToolResult, CallToolError> {
        let pattern = params.pattern.unwrap_or("**/*".to_string());
        let result_content = context
            .zip_directory(params.input_directory, pattern, params.target_zip_file)
            .await
            .map_err(CallToolError::new)?;
        //TODO: return resource?
        Ok(CallToolResult::text_content(result_content, None))
    }
}
