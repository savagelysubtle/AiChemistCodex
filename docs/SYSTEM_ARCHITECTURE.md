# 🏛️ AiChemist Codex: System Architecture Overview

The AiChemist Codex is envisioned as a suite of interconnected, intelligent tools, each specializing in a core aspect of knowledge management, processing, and transformation. While each component (`Archivum`, `Compendium`, `Transmutations`) is an independent project with its own detailed architecture, they are designed with the potential for future synergy and integration in mind.

This document provides a high-level overview and links to the specific architectural details for each pillar of the Codex.

## Core Architectural Philosophy

*   **Modularity**: Each project is self-contained, allowing for independent development, deployment, and evolution.
*   **Clear Interfaces**: Projects will expose well-defined APIs (CLI, gRPC, Python libraries) to facilitate interaction and potential future integration.
*   **Focused Responsibility**: Each tool addresses a distinct domain of functionality (file management & search, external knowledge integration, document conversion).

## Project-Specific Architectures

Delve into the specific architectural design of each AiChemist project through the links below:

### 🧪 AiChemist Archivum

The Archivum is designed for AI-driven file management, ingestion, tagging, and multi-faceted search capabilities.
*   **Detailed Architecture**: [View Archivum Architecture](./../AiChemistArchivum/docs/ARCHITECTURE.md)
    *   This document outlines its layered design, from core domain logic to service orchestration and interface delivery (CLI, gRPC, Electron).

### 📚 AiChemist Compendium

The Compendium serves as an MCP (Model Context Protocol) server, enabling AI assistants to interact with knowledge bases like Obsidian vaults.
*   **Detailed Architecture**: [View Compendium MCP Architecture](./../AiChemistCompendium/docs-obsidian/projects/myMcpServer/architecture/overview.md)
    *   This document describes its microservices approach, including the MCP Client, Proxy Connection Server, Core Layer, and Tool Servers.

### 🔄 AiChemist Transmutations

The Transmutation Codex is a Python library focused on robust document format conversion, including OCR capabilities.
*   **Design Decisions & Architecture**: [View Transmutations Design Decisions](./../AiChemistTransmutations/docs/source/architecture/design_decisions.rst)
    *   **Note**: This document is in reStructuredText (.rst) format. It provides an in-depth look at converter architecture, technology choices (Ruff, mypy, Sphinx), testing strategy, and a detailed converter matrix. It is best viewed rendered (e.g., via Sphinx) or as plain text.

## Future Suite-Level Integration

While currently distinct, future development may explore:
*   A unified API gateway for accessing functionalities across all projects.
*   Shared data models or libraries for common entities.
*   Cross-project workflows (e.g., ingesting a document with Archivum, converting it with Transmutations, and then referencing it via Compendium).

This architectural overview will evolve as the AiChemist Codex matures.