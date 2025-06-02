# AiChemist Codex Workspace Context

This document provides a high-level overview of the **AiChemist Codex** repository, its structure, key projects, and guiding principles.

## Repository Overview

The `AiChemistCodex` is the central hub for a suite of AI-powered tools designed for developers and researchers. It acts as a parent container for several independent projects, each residing in its own Git repository within their respective subdirectories.

**Main Repository README**: [README.md](mdc:README.md)

## Key Projects

The Codex currently comprises the following core projects:

1.  **[🧪 AiChemistArchivum](./AiChemistArchivum/README.md)** ([view README](mdc:AiChemistArchivum/README.md))
    *   An AI-driven file-management platform for ingesting, tagging, versioning, and querying content.
2.  **[📚 AiChemistCompendium](./AiChemistCompendium/README.md)** ([view README](mdc:AiChemistCompendium/README.md))
    *   The central knowledge hub for all AiChemist projects and research, formerly housing an MCP server.
3.  **[🔄 AiChemistTransmutations](./AiChemistTransmutations/README.md)** ([view README](mdc:AiChemistTransmutations/README.md))
    *   A Python library for converting between different document formats (Markdown, PDF, HTML) with OCR support.
4.  **[🛠️ AiChemistForge](./AiChemistForge/README.md)** ([view README](mdc:AiChemistForge/README.md))
    *   A workspace for developing Model Context Protocol (MCP) servers and a collection of tools/utilities.

## Core Philosophy & Structure

Each project within the Codex is maintained in its own Git repository to allow for independent evolution while being part of a cohesive suite. The `AiChemistCodex` provides an overarching structure, ecosystem-wide documentation, and coordination.

For a deeper understanding of the project's narrative and naming, refer to:
*   **[📜 The AiChemist's Codex: A Chronicle of Digital Alchemy](./docs/THE_AICHEMISTS_CODEX.md)** ([view Chronicle](mdc:docs/THE_AICHEMISTS_CODEX.md))

## Guiding Rules & Personas

This workspace is guided by specific rules and personas defined in the `.cursor/rules/` directory:

*   **Repository Maintainer Persona**: [`repository-maintainer-persona.mdc`](mdc:.cursor/rules/repository-maintainer-persona.mdc) - Defines the assistant's role in maintaining this repository.
*   **Documentation Standard**: [`002-catalyst-documentation-standard.mdc`](mdc:.cursor/rules/002-catalyst-documentation-standard.mdc) - Outlines the documentation standards to be upheld.

## Key Architectural & Project Documentation

For more detailed insights into the system and individual projects:

*   **[🏛️ System Architecture Overview](./docs/SYSTEM_ARCHITECTURE.md)** ([view System Architecture](mdc:docs/SYSTEM_ARCHITECTURE.md))
*   **[📚 Project Documentation Hub](./docs/PROJECT_DOCUMENTATION_HUB.md)** ([view Project Documentation Hub](mdc:docs/PROJECT_DOCUMENTATION_HUB.md))

This context file should help any collaborator (including myself, your AI assistant) quickly grasp the essentials of the AiChemist Codex.