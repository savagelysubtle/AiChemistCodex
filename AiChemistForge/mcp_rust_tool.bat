@echo off
setlocal

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