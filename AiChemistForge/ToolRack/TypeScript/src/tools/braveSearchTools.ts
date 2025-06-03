// import { log } from '../../../brave-search/src/logger.js'; // Import the logger
import { z, ZodRawShape } from 'zod'; // Import Zod and ZodRawShape

console.error('[TOOLS.TS] Module start.'); // Use console.error
console.error(`[TOOLS.TS] BRAVE_API_KEY in process.env at module start: ${process.env.BRAVE_API_KEY ? 'Exists' : 'DOES NOT EXIST'}`); // Use console.error

import {
  // CallToolRequestSchema, // Will be handled in server.ts
  // ListToolsRequestSchema, // Will be handled in server.ts
  Tool,
  TextContent, // For return type
  CallToolResult, // For return type
} from "@modelcontextprotocol/sdk/types.js";

// Define Zod Schema SHAPES (for McpServer.tool)
export const BraveWebSearchShape: ZodRawShape = {
  query: z.string().describe("Search query (max 400 chars, 50 words)"),
  count: z.number().default(10).describe("Number of results (1-20, default 10)").optional(),
  offset: z.number().default(0).describe("Pagination offset (max 9, default 0)").optional(),
};

export const BraveCodeSearchShape: ZodRawShape = {
  query: z.string().describe("Code search query (e.g. 'github repository for brave search')"),
  count: z.number().default(10).describe("Number of results (1-20, default 10)").optional(),
};

// Define Zod Schema INSTANCES (for z.infer and potentially other uses)
export const BraveWebSearchZodSchema = z.object(BraveWebSearchShape);
export const BraveCodeSearchZodSchema = z.object(BraveCodeSearchShape);

// Exporting tool definitions with PLAIN OBJECT schemas
export const WEB_SEARCH_TOOL: Tool = {
  name: "brave_web_search",
  description:
    "Performs a web search using the Brave Search API, ideal for general queries, news, articles, and online content. " +
    "Use this for broad information gathering, recent events, or when you need diverse web sources. " +
    "Supports pagination, content filtering, and freshness controls. " +
    "Maximum 20 results per request, with offset for pagination. ",
  inputSchema: { // Plain object schema for Tool type compatibility
    type: "object",
    properties: {
      query: { type: "string", description: "Search query (max 400 chars, 50 words)" },
      count: { type: "number", default: 10, description: "Number of results (1-20, default 10)" },
      offset: { type: "number", default: 0, description: "Pagination offset (max 9, default 0)" },
    },
    required: ["query"],
  },
  annotations: {
    title: "Brave Web Search",
    readOnlyHint: true,
    destructiveHint: false,
    idempotentHint: true, // Assuming repeated calls with same args have no *additional side effect on the server*, results may change
    openWorldHint: true,
  },
};

export const CODE_SEARCH_TOOL: Tool = {
  name: "brave_code_search",
  description:
    "Searches developer-focused sites like Stack Overflow, GitHub, MDN, and technical subreddits using Brave Search. " +
    "Ideal for finding code snippets, technical documentation, programming discussions, and solutions to coding problems. " +
    "Uses targeted site search for relevance. Supports result count customization. " +
    "Maximum 20 results per request.",
  inputSchema: { // Plain object schema
    type: "object",
    properties: {
      query: { type: "string", description: "Code search query (e.g. 'github repository for brave search')" },
      count: { type: "number", default: 10, description: "Number of results (1-20, default 10)" },
    },
    required: ["query"],
  },
  annotations: {
    title: "Brave Code Search",
    readOnlyHint: true,
    destructiveHint: false,
    idempotentHint: true,
    openWorldHint: true,
  },
};

// Check for API key - this needs to be accessible by the execution logic.
// It's fine for it to be a module-level constant checked once.
console.error("[TOOLS.TS] About to check BRAVE_API_KEY value."); // Use console.error
const BRAVE_API_KEY = process.env.BRAVE_API_KEY!;
if (!BRAVE_API_KEY) {
  // Log to stderr and throw to prevent the module from being used incorrectly if key is missing
  console.error("CRITICAL: BRAVE_API_KEY environment variable is required for braveSearchTools module."); // Use console.error
  throw new Error("BRAVE_API_KEY environment variable is required.");
}

const RATE_LIMIT = {
  perSecond: 1,
  perMonth: 15000
};

let requestCount = {
  second: 0,
  month: 0,
  lastReset: Date.now()
};

function checkRateLimit() {
  const now = Date.now();
  // Reset per-second counter
  if (now - requestCount.lastReset > 1000) {
    requestCount.second = 0;
    requestCount.lastReset = now;
  }
  // Check limits
  if (requestCount.second >= RATE_LIMIT.perSecond || requestCount.month >= RATE_LIMIT.perMonth) {
    // This error will be caught by the tool execution wrapper and returned as an MCP error
    throw new Error('Brave Search API rate limit exceeded.');
  }
  requestCount.second++;
  requestCount.month++;
}

// Inferred types for function signatures
export type BraveWebSearchArgs = z.infer<typeof BraveWebSearchZodSchema>;
export type BraveCodeSearchArgs = z.infer<typeof BraveCodeSearchZodSchema>;

interface BraveWeb {
  web?: {
    results?: Array<{
      title: string;
      description: string;
      url: string;
      language?: string;
      published?: string;
      rank?: number;
    }>;
  };
  // locations part can be removed if local search is fully gone
}

// Core search logic - remains largely the same but will be called by exported execution functions
async function performBraveSearch(query: string, count: number = 10, offset: number = 0): Promise<string> {
  checkRateLimit(); // Checks rate limit before each API call
  const url = new URL('https://api.search.brave.com/res/v1/web/search');
  url.searchParams.set('q', query);
  url.searchParams.set('count', Math.min(count, 20).toString()); // API limit
  url.searchParams.set('offset', Math.max(0, Math.min(offset, 9)).toString()); // API limits for offset

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

  try {
    const response = await fetch(url, {
      signal: controller.signal,
      headers: {
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip',
        'X-Subscription-Token': BRAVE_API_KEY
      }
    });

    if (!response.ok) {
      // Throw an error that will be caught by the calling function and formatted as an MCP error
      throw new Error(`Brave API error: ${response.status} ${response.statusText}. Details: ${await response.text()}`);
    }

    const data = await response.json() as BraveWeb;

    const results = (data.web?.results || []).map(result => ({
      title: result.title || 'N/A', // Provide fallback for missing fields
      description: result.description || 'N/A',
      url: result.url || '#'
    }));

    if (results.length === 0) {
      return "No results found for your query.";
    }

    return results.map(r =>
      `Title: ${r.title}
Description: ${r.description}
URL: ${r.url}`
    ).join('\n\n');
  } finally {
    clearTimeout(timeoutId);
  }
}

// Exported execution function for Web Search
export async function executeWebSearch(args: BraveWebSearchArgs): Promise<CallToolResult> {
  const { query, count = 10, offset = 0 } = args;
  try {
    const resultsText = await performBraveSearch(query, count, offset);
    return {
      content: [{ type: "text", text: resultsText } as TextContent],
      isError: false,
    };
  } catch (error) {
    console.error('Error during performBraveSearch (web)', { query, count, offset, error }); // Log error context
    return {
      content: [{ type: "text", text: `Error during web search: ${error instanceof Error ? error.message : String(error)}` } as TextContent],
      isError: true,
    };
  }
}

// Exported execution function for Code Search
export async function executeCodeSearch(args: BraveCodeSearchArgs): Promise<CallToolResult> {
  const { query: userQuery, count = 10 } = args;

  const siteFilters = [
    "site:stackoverflow.com",
    "site:github.com",
    "site:developer.mozilla.org",
    "site:*.stackexchange.com", // Broader Stack Exchange
    "site:reddit.com/r/programming",
    "site:reddit.com/r/learnprogramming",
    "site:dev.to",
    "site:medium.com", // Often has technical articles
    // Consider official documentation sites for popular languages/frameworks if desired
    // e.g., site:docs.python.org, site:reactjs.org
  ].join(" OR ");

  const finalQuery = `${userQuery} (${siteFilters})`;

  try {
    // Using offset 0 for code search as complex site filters might not paginate predictably
    const resultsText = await performBraveSearch(finalQuery, count, 0);
    return {
      content: [{ type: "text", text: resultsText } as TextContent],
      isError: false,
    };
  } catch (error) {
    console.error('Error during performBraveSearch (code)', { finalQuery, count, error }); // Log error context
    return {
      content: [{ type: "text", text: `Error during code search: ${error instanceof Error ? error.message : String(error)}` } as TextContent],
      isError: true,
    };
  }
}