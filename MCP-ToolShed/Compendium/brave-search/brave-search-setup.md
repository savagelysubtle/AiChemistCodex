# Brave Search API Setup and Configuration

## What is the Brave Search API?

The Brave Search API is a powerful search service provided by Brave Software that allows developers to integrate search functionality into their applications. It offers a range of capabilities including:

- General web search functionality
- Local business and place search
- Specialized code search for programming-related queries
- Rate limiting controls
- Result filtering and pagination

The API provides access to Brave's independent search index, which emphasizes privacy and unbiased results compared to other search engines.

## Configuration Process

### Setting Up in `.roo/mcp.json`

The Brave Search API is configured as an MCP (Model Context Protocol) server in the `.roo/mcp.json` file. This allows the API to be accessed as a tool within the Roo environment.

Here's the configuration structure:

```json
{
  "mcpServers": {
    "brave-search-Local": {
      "command": "node",
      "type": "stdio",
      "args": ["path/to/ToolRack/brave-search/run.js"],
      "env": {
        "BRAVE_API_KEY": "Brave_api_key"
      },
      "disabled": false,
      "alwaysAllow": ["brave_code_search", "brave_web_search"]
    }
  }
}
```

Key configuration elements:

- **Server name**: `brave-search-Local` - The identifier for the MCP server
- **Command**: `node` - The command to run the server
- **Type**: `stdio` - The communication protocol (standard input/output)
- **Args**: Path to the run.js file that launches the server
- **Env**: Environment variables, including the Brave API key
- **alwaysAllow**: Tools that are always allowed to be used without additional permissions

### Environment Variables in `.env.local`

The Brave Search API key is stored in the `.env.local` file to keep it secure and separate from the code:

```
BRAVE_API_KEY=Brave_api_key
```

This file should be kept private and not committed to version control. The `run.js` script uses the `dotenvx` package to load this environment variable when starting the server.

### Obtaining a Brave API Key

To use the Brave Search API, you need to:

1. Visit the [Brave Search Developer Portal](https://search.brave.com/api/)
2. Create a developer account
3. Generate an API key
4. Add the key to your `.env.local` file

## Troubleshooting the SUBSCRIPTION_TOKEN_INVALID Error

If you encounter a `SUBSCRIPTION_TOKEN_INVALID` error when using the Brave Search API, follow these steps:

1. **Verify your API key**: Ensure the API key in your `.env.local` file is correct and hasn't expired.

2. **Check rate limits**: The Brave Search API has rate limits (1 request per second, 15,000 requests per month). Exceeding these limits can cause authentication errors.

3. **Inspect the error response**: The full error message may contain additional details:

   ```
   Brave API error: 401 Unauthorized
   {"error":"SUBSCRIPTION_TOKEN_INVALID"}
   ```

4. **Regenerate your API key**: If the key is invalid, generate a new one from the Brave Search Developer Portal.

5. **Verify environment variable loading**: Ensure the `.env.local` file is being properly loaded. The server logs should show:

   ```
   Successfully loaded environment variables from .env.local
   ```

6. **Check for API changes**: The Brave Search API may occasionally change its authentication methods. Check the official documentation for updates.

## Using the brave_code_search Tool

The `brave_code_search` tool is specialized for programming-related queries. It enhances search queries to find code snippets, documentation, and developer resources.

### Basic Usage

```json
{
  "query": "implement binary search"
}
```

### Language-Specific Search

```json
{
  "query": "async/await example",
  "language": "javascript"
}
```

### Site-Specific Search

```json
{
  "query": "react hooks tutorial",
  "site": "github.com"
}
```

### Combined Filters

```json
{
  "query": "implement quicksort",
  "language": "python",
  "site": "stackoverflow.com",
  "count": 5
}
```

### How It Works

The `brave_code_search` tool:

1. Enhances your query with programming context if not already present
2. Adds language-specific terms when a language is specified
3. Adds site-specific filtering when a site is specified
4. Formats results to highlight:
   - Source type (Repository, Documentation, Q&A)
   - Domain information
   - Programming language context
   - Description and URL

### Result Format

Results are formatted in a developer-friendly way:

```
Title: [Result Title]
Source: [Source Site] ([Type: Documentation/Repository/Q&A])
Language: [Detected Programming Language]
Description: [Result Description]
URL: [Result URL]
```

This format makes it easy to quickly identify the most relevant resources for your programming needs.

## Additional Resources

The Brave Search MCP server also provides several resources that can be accessed:

- `brave-search://metadata/trending` - Currently trending search topics
- `brave-search://web/popular-queries/{category}` - Pre-cached results for common queries
- `brave-search://docs/api-reference` - Documentation about the API
- `brave-search://docs/usage-examples` - Examples of how to use the tools
- `brave-search://history/recent` - Recent searches performed through the MCP server
