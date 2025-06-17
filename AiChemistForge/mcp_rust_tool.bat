@echo off
setlocal

set "RUST_TOOLCHAIN_PATH=D:\ProgramData\CodingLanguages\Rust\.cargo\bin"
set "PATH=%RUST_TOOLCHAIN_PATH%;%PATH%"
set "RUST_LOG=debug"

npx @modelcontextprotocol/inspector ^
  uv ^
  --directory "D:/Coding/AiChemistCodex/AiChemistForge/ToolRack/Rust/" ^
  run cargo ^
  run ^
  --manifest-path "D:/Coding/AiChemistCodex/AiChemistForge/ToolRack/Rust/Cargo.toml" ^
  -- ^
  --allow-write ^
  "D:/Coding/AiChemistCodex/AiChemistForge/ToolRack/Rust/test_files" ^
  "F:/" ^
  "D:/"

endlocal