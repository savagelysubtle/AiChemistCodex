# 🧙‍♂️ AiChemist Codex 🧪

Welcome to the AiChemist Codex! This is the central hub for a suite of AI-powered tools designed for developers and researchers.

This repository acts as a parent container for several independent projects, each residing in its own Git repository within their respective subdirectories.

## Projects

The Codex currently comprises the following projects:

1.  **[🧪 AiChemist Archivum](./AiChemistArchivum/README.md)**
    *   An AI-driven file-management platform.
    *   Manages and queries content via embeddings, regex, or semantic search.
    *   Exposes workflows through CLI, gRPC/JSON API, and a desktop GUI.
    *   *Independent Git Repository located in: `./AiChemistArchivum/`*
    *   See its [README](./AiChemistArchivum/README.md) for more details.

2.  **[📚 AiChemist Compendium](./AiChemistCompendium/README.md)**
    *   An MCP (Model Context Protocol) server.
    *   Enables AI assistants to interact with Obsidian vaults.
    *   Provides tools for reading, creating, editing, and managing notes and tags.
    *   *Independent Git Repository located in: `./AiChemistCompendium/`*
    *   See its [README](./AiChemistCompendium/README.md) for more details.

3.  **[🔄 AiChemist Transmutations](./AiChemistTransmutations/README.md)**
    *   A Python library for converting between different document formats (Markdown, PDF, HTML).
    *   Features OCR support for scanned documents.
    *   Offers CLI, GUI, and Electron bridge interfaces.
    *   *Independent Git Repository located in: `./AiChemistTransmutations/`*
    *   See its [README](./AiChemistTransmutations/README.md) for more details.

## Structure & Philosophy

Each project within the Codex (`Archivum`, `Compendium`, `Transmutations`) is maintained in its own Git repository. This parent `AiChemistCodex` repository is intended to:
-   Provide an overarching structure and entry point to the suite.
-   Hold documentation and resources relevant to the entire AiChemist ecosystem.
-   Facilitate coordination if needed, without entangling the individual project histories.

To work with an individual project, navigate to its subdirectory (e.g., `cd AiChemistArchivum`) and use Git commands as you normally would for any standalone repository.

This setup allows for both separation of concerns and co-location, ensuring that each project can evolve independently while being part of a larger, cohesive suite.

## Delve Deeper: The AiChemist's Lore

To understand the philosophy, the naming conventions, and the overarching narrative behind the AiChemist suite, explore the chronicle within:

*   **[📜 The AiChemist's Codex: A Chronicle of Digital Alchemy](./docs/THE_AICHEMISTS_CODEX.md)**

## 📖 Suite Documentation

For a deeper dive into the technical aspects and project-specific details, explore the following resources:

*   **[🏛️ System Architecture Overview](./docs/SYSTEM_ARCHITECTURE.md)**: Understand the high-level architecture of the AiChemist Codex and how individual projects are designed.
*   **[📚 Project Documentation Hub](./docs/PROJECT_DOCUMENTATION_HUB.md)**: Access detailed READMEs, architecture documents, roadmaps, and feature guides for each individual project (`Archivum`, `Compendium`, `Transmutations`).