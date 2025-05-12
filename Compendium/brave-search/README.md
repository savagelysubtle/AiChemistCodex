# @compendium/brave-search

This package provides a Model Context Protocol (MCP) tool server that exposes Brave Search API functionality. It allows language models or other MCP clients to perform web searches and local business lookups using Brave's search infrastructure.

## Features

* **Web Search:** Provides a `brave_web_search` tool for general web queries.
* **Local Search:** Provides a `brave_local_search` tool for finding businesses and places, with fallback to web search if no local results are found.
* **MCP Compliant:** Communicates using the Model Context Protocol over standard input/output (stdio).
* **API Key Authentication:** Uses the `BRAVE_API_KEY` environment variable for authentication.
* **Basic Rate Limiting:** Implements simple per-second rate limiting.

## Prerequisites

* **Node.js:** Version 14 or higher (due to ES2020 target in `tsconfig.json`).
* **Brave Search API Key:** You need a valid API key from Brave. Obtain one from the Brave Search API website.

## Installation

This tool is typically used within the Compendium ecosystem. Refer to the main Compendium documentation for integration details.

If running standalone or during development, install dependencies:

```bash
# Using npm
npm install

# Or using pnpm
pnpm install

# Or using yarn
yarn install
```

## Configuration

The server requires the BRAVE_API_KEY environment variable to be set with your valid Brave Search API key.

```bash

export BRAVE_API_KEY="YOUR_ACTUAL_API_KEY"
If this variable is not set, the server will log an error and exit upon startup.
```

## Building

The server is written in TypeScript and needs to be compiled to JavaScript before running:

```bash

# Using npm

npm run build

# Or directly using tsc (if installed globally or via npx)

npx tsc
```

This will compile the index.ts file into the dist/ directory.

### Running the Tool Server

Once built and configured, run the server using Node.js:

```bash
# Ensure BRAVE_API_KEY is set in your environment
node dist/index.js
```

The server will start listening for MCP requests on stdin and send responses to stdout. You should see log messages on stderr indicating the server's status (e.g., "Brave Search MCP Server running on stdio").

### Available Tools

The server exposes the following tools:

1. brave_web_search
Description: Performs a general web search using the Brave Search API. Suitable for broad information gathering, news, articles, recent events, and diverse web sources. Supports pagination.
Input Schema:
query (string, required): The search query (max 400 chars, 50 words).
count (number, optional, default: 10): Number of results to return (1-20).
offset (number, optional, default: 0): Pagination offset for results (max 9).
Output: A plain text string containing the search results, formatted as:
plaintext
Title: [Result Title]
Description: [Result Description]
URL: [Result URL]

Title: [Next Result Title]

2. brave_local_search
Description: Searches for local businesses and places (restaurants, services, etc.). Ideal for queries implying location ("near me", specific places). Returns details like address, phone, ratings, hours. Falls back to brave_web_search if no specific local results are found for the query.
Input Schema:
query (string, required): The local search query (e.g., "coffee shops near downtown").
count (number, optional, default: 5): Maximum number of local results to retrieve details for (1-20). Note: The underlying API calls might fetch slightly differently, but this controls the final formatted output count.
Output: A plain text string containing details for each local result found, formatted as:
plaintext
Name: [Business Name]
Address: [Full Address]
Phone: [Phone Number or N/A]
Rating: [Rating Value or N/A] ([Review Count] reviews)
Price Range: [Price Range or N/A]
Hours: [Opening Hours or N/A]
Description: [Business Description or 'No description available']

Name: [Next Business Name]

If no local results are found, the output will be the same as brave_web_search for the same query and count. If neither local nor web fallback yields results, it may return "No local results found" or an empty string depending on the API response.
Rate Limiting
The server implements basic rate limiting:

Per Second: Maximum 1 request per second.
Per Month (Theoretical): Tracks monthly requests but does not automatically reset the counter monthly. The server needs to be restarted for the monthly count to reset. The limit is set to 15,000.
Exceeding the rate limit will result in an error response from the tool call.

Development
Build: npm run build or tsc
Linting/Formatting: (Add details if linters/formatters like ESLint/Prettier are configured)
Testing: (Add details if tests are available)
License
(Specify License Here - e.g., MIT, Apache 2.0)
