# Brave Search MCP Server

This MCP server provides tools to interact with the Brave Search API, allowing for regular web searches and code-focused searches.

## Prerequisites

*   Node.js (v18 or later recommended)
*   npm (comes with Node.js)

## Setup

1.  **Clone the repository (if applicable) or ensure you have the `ToolRack/brave-search` directory.**
2.  **Navigate to the server directory:**
    ```bash
    cd path/to/ToolRack/brave-search
    ```
3.  **Create a local environment file:**
    Copy `.env.example` to `.env.local`:
    ```bash
    cp .env.example .env.local
    ```
    Then, edit `.env.local` and add your Brave API Key:
    ```
    BRAVE_API_KEY=YOUR_ACTUAL_BRAVE_API_KEY
    ```
4.  **Install dependencies:**
    ```bash
    npm install
    ```

## Build

To compile the TypeScript code, run:

```bash
npm run build
```

This will output the JavaScript files to the `dist/` directory.

## Run

To start the MCP server:

```bash
npm run start
```

The server will connect and listen on stdio for MCP requests.

For development, you can use:
```bash
npm run dev
```
This will watch for changes in the `src/` directory, recompile, and restart the server.

## Tools Provided

### 1. `regularSearch`

Performs a regular web search using the Brave Search API and returns a list of web pages.

**Input Schema:**

```json
{
  "query": "string", // The search query (cannot be empty)
  "count": "number"  // Optional: Number of results to return (integer, positive, default: 10)
}
```

**Example Input:**

```json
{
  "query": "latest TypeScript features",
  "count": 5
}
```

**Output Schema:**

```json
{
  "results": [
    {
      "title": "string",
      "url": "string (url)",
      "description": "string (optional)",
      "age": "string (optional, e.g., '1 day ago')"
    }
  ]
}
```

**Example Output:**

```json
{
  "results": [
    {
      "title": "Announcing TypeScript 5.0 - TypeScript",
      "url": "https://devblogs.microsoft.com/typescript/announcing-typescript-5-0/",
      "description": "Today we're excited to announce the release of TypeScript 5.0! If you're not yet familiar with TypeScript...",
      "age": "1 year ago"
    }
    // ... more results
  ]
}
```

### 2. `codeSearch`

Performs a code-focused search using Brave Search API, prioritizing code repositories, software pages, and technical discussions.

**Input Schema:**

```json
{
  "query": "string", // The search query, ideally focused on code (cannot be empty)
  "count": "number"  // Optional: Number of code-related results to return (integer, positive, default: 5)
}
```

**Example Input:**

```json
{
  "query": "React state management library",
  "count": 3
}
```

**Output Schema:**

```json
{
  "results": [
    {
      "title": "string",
      "url": "string (url)",
      "description": "string (optional)",
      "type": "string (optional, enum: [\"web\", \"software\", \"discussion\", \"code_infobox\"])",
      "language": "string (optional, e.g., 'JavaScript')",
      "repo": "string (optional, url, e.g., repository URL)",
      "stars": "number (optional)",
      "age": "string (optional, e.g., '2 weeks ago')"
    }
  ]
}
```

**Example Output:**

```json
{
  "results": [
    {
      "title": "Zustand - Bear-bones state-management for React",
      "url": "https://github.com/pmndrs/zustand",
      "description": "A small, fast and scalable bearbones state-management solution. Zustand has a comfy api based on hooks.",
      "type": "software",
      "language": "TypeScript",
      "repo": "https://github.com/pmndrs/zustand",
      "stars": 25000,
      "age": "3 months ago"
    }
    // ... more results
  ]
}
```