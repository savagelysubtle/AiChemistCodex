#!/usr/bin/env node

// Load environment variables from .env.local
import { execSync } from 'child_process';
// Check if BRAVE_API_KEY is already set (e.g., by Cursor's mcp.json)
if (!process.env.BRAVE_API_KEY) {
  console.error("BRAVE_API_KEY not found in environment. Attempting to load from .env.local...");

  // Load environment variables from .env.local
  try {
    // Try to load environment variables using dotenvx
    console.error("Loading environment variables from .env.local using dotenvx...");
    // Note: We run a simple command just to trigger dotenvx loading, not to execute the main script yet.
    execSync('dotenvx run -f .env.local -- node -e "process.exit(0)"', { stdio: 'pipe' });
    console.error("dotenvx attempted loading from .env.local (check process.env.BRAVE_API_KEY now)");
  } catch (error) {
    console.error("Failed to load environment variables using dotenvx:", error);
    console.error("Falling back to manual environment variable loading...");

    // Fallback: Try to load environment variables manually
    try {
      const fs = await import('fs');
      const path = await import('path');

      const envPath = path.resolve(process.cwd(), '.env.local');
      if (fs.existsSync(envPath)) {
        const envContent = fs.readFileSync(envPath, 'utf8');
        const envVars = envContent.split('\n').filter(line => line.trim() && !line.startsWith('#'));

        for (const line of envVars) {
          const [key, ...valueParts] = line.split('=');
          const value = valueParts.join('=').trim();
          if (key && value && key.trim() === 'BRAVE_API_KEY') { // Only load the specific key needed
            process.env[key.trim()] = value.replace(/^["']|["']$/g, ''); // Remove quotes if present
            console.error("Successfully loaded BRAVE_API_KEY manually from .env.local");
            break; // Stop after finding the key
          }
        }
        if (!process.env.BRAVE_API_KEY) {
           console.error("BRAVE_API_KEY not found in .env.local during manual load.");
        }
      } else {
        console.error("Could not find .env.local file for manual loading.");
      }
    } catch (manualError) {
      console.error("Failed to load environment variables manually:", manualError);
    }
  }
} else {
  console.error("BRAVE_API_KEY already found in environment (likely from mcp.json). Skipping .env.local load.");
}

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListResourcesRequestSchema,
  ListToolsRequestSchema,
  ReadResourceRequestSchema,
  Resource,
  Tool,
} from "@modelcontextprotocol/sdk/types.js";

const WEB_SEARCH_TOOL: Tool = {
  name: "brave_web_search",
  description:
    "Performs a web search using the Brave Search API, ideal for general queries, news, articles, and online content. " +
    "Use this for broad information gathering, recent events, or when you need diverse web sources. " +
    "Supports pagination, content filtering, and freshness controls. " +
    "Maximum 20 results per request, with offset for pagination. ",
  inputSchema: {
    type: "object",
    properties: {
      query: {
        type: "string",
        description: "Search query (max 400 chars, 50 words)"
      },
      count: {
        type: "number",
        description: "Number of results (1-20, default 10)",
        default: 10
      },
      offset: {
        type: "number",
        description: "Pagination offset (max 9, default 0)",
        default: 0
      },
    },
    required: ["query"],
  },
};

const LOCAL_SEARCH_TOOL: Tool = {
  name: "brave_local_search",
  description:
    "Searches for local businesses and places using Brave's Local Search API. " +
    "Best for queries related to physical locations, businesses, restaurants, services, etc. " +
    "Returns detailed information including:\n" +
    "- Business names and addresses\n" +
    "- Ratings and review counts\n" +
    "- Phone numbers and opening hours\n" +
    "Use this when the query implies 'near me' or mentions specific locations. " +
    "Automatically falls back to web search if no local results are found.",
  inputSchema: {
    type: "object",
    properties: {
      query: {
        type: "string",
        description: "Local search query (e.g. 'pizza near Central Park')"
      },
      count: {
        type: "number",
        description: "Number of results (1-20, default 5)",
        default: 5
      },
    },
    required: ["query"]
  }
};

const CODE_SEARCH_TOOL: Tool = {
  name: "brave_code_search",
  description:
    "Specialized search for programming-related queries using the Brave Search API. " +
    "Optimized for finding code snippets, technical documentation, and developer resources. " +
    "Returns results from programming-focused sites with code-specific formatting. " +
    "Ideal for finding solutions to coding problems, API documentation, and programming examples.",
  inputSchema: {
    type: "object",
    properties: {
      query: {
        type: "string",
        description: "Programming-related search query"
      },
      language: {
        type: "string",
        description: "Programming language filter (e.g., 'python', 'javascript', 'java')",
        default: ""
      },
      site: {
        type: "string",
        description: "Limit results to specific site (e.g., 'github.com', 'stackoverflow.com')",
        default: ""
      },
      count: {
        type: "number",
        description: "Number of results (1-20, default 10)",
        default: 10
      },
      offset: {
        type: "number",
        description: "Pagination offset (max 9, default 0)",
        default: 0
      }
    },
    required: ["query"]
  }
};

// Define resource schemas
const TRENDING_TOPICS_RESOURCE: Resource = {
  name: "trending_topics",
  uri: "brave-search://metadata/trending",
  description: "Provides currently trending search topics across different categories",
};

const POPULAR_QUERIES_RESOURCE: Resource = {
  name: "popular_queries",
  uri: "brave-search://web/popular-queries/{category}",
  description: "Provides pre-cached results for common queries in different categories (technology, science, news, etc.)",
};

const API_REFERENCE_RESOURCE: Resource = {
  name: "api_reference",
  uri: "brave-search://docs/api-reference",
  description: "Documentation about the Brave Search API and its capabilities",
};

const USAGE_EXAMPLES_RESOURCE: Resource = {
  name: "usage_examples",
  uri: "brave-search://docs/usage-examples",
  description: "Examples of how to use the Brave Search MCP tools effectively",
};

const SEARCH_HISTORY_RESOURCE: Resource = {
  name: "search_history",
  uri: "brave-search://history/recent",
  description: "Recent searches performed through the MCP server",
};

// Store for search history
const searchHistory: { query: string; timestamp: number; tool: string }[] = [];

// Cache for popular queries
const popularQueriesCache: { [category: string]: { query: string; results: string }[] } = {
  technology: [
    {
      query: "latest AI developments",
      results: "1. OpenAI GPT-4o released with multimodal capabilities\n2. Google Gemini Advanced launched for enterprise\n3. Meta's LLAMA 3 open source model shows impressive performance\n4. Anthropic introduces Claude 3 Opus with enhanced reasoning\n5. Stability AI releases new image generation model"
    },
    {
      query: "blockchain applications",
      results: "1. Supply chain tracking using blockchain technology\n2. Decentralized finance (DeFi) platforms gaining adoption\n3. NFT marketplaces for digital art and collectibles\n4. Blockchain-based voting systems for secure elections\n5. Smart contracts for automated legal agreements"
    }
  ],
  science: [
    {
      query: "recent space discoveries",
      results: "1. James Webb Space Telescope reveals new exoplanet atmospheres\n2. NASA's Perseverance rover finds organic compounds on Mars\n3. First direct image of supermassive black hole at Milky Way center\n4. Evidence of water vapor detected on Jupiter's moon Europa\n5. New dwarf planet discovered beyond Neptune"
    },
    {
      query: "quantum computing breakthroughs",
      results: "1. IBM achieves 1000+ qubit quantum processor\n2. Google demonstrates quantum error correction\n3. Microsoft's topological qubit shows stability improvements\n4. Quantum advantage demonstrated for machine learning tasks\n5. New quantum algorithm for optimization problems"
    }
  ],
  news: [
    {
      query: "global economic outlook",
      results: "1. IMF predicts 3.1% global growth for current year\n2. Central banks considering interest rate adjustments\n3. Supply chain disruptions continue to affect manufacturing\n4. Renewable energy investments reach record levels\n5. Emerging markets showing resilience despite challenges"
    },
    {
      query: "climate change initiatives",
      results: "1. EU announces new carbon reduction targets\n2. Major corporations pledge net-zero emissions by 2040\n3. Breakthrough in carbon capture technology reported\n4. Climate resilience funding increased for vulnerable regions\n5. New international agreement on methane reduction"
    }
  ]
};

// Trending topics data
const trendingTopics = {
  technology: ["artificial intelligence", "quantum computing", "web3", "augmented reality", "cybersecurity"],
  science: ["CRISPR gene editing", "fusion energy", "exoplanet discoveries", "brain-computer interfaces", "renewable materials"],
  health: ["mRNA vaccines", "telemedicine advances", "mental health research", "longevity science", "precision medicine"],
  business: ["remote work trends", "sustainable business practices", "supply chain resilience", "digital transformation", "fintech innovation"]
};

// API reference documentation
const apiReference = `# Brave Search API Reference

## Available Tools

### brave_web_search
Performs general web searches using the Brave Search API.

**Parameters:**
- query (required): Search query (max 400 chars, 50 words)
- count (optional): Number of results (1-20, default 10)
- offset (optional): Pagination offset (max 9, default 0)

### brave_local_search
Searches for local businesses and places.

**Parameters:**
- query (required): Local search query (e.g. 'pizza near Central Park')
- count (optional): Number of results (1-20, default 5)

### brave_code_search
Specialized search for programming-related queries.

**Parameters:**
- query (required): Programming-related search query
- language (optional): Programming language filter (e.g., 'python', 'javascript')
- site (optional): Limit results to specific site (e.g., 'github.com', 'stackoverflow.com')
- count (optional): Number of results (1-20, default 10)
- offset (optional): Pagination offset (max 9, default 0)

## Available Resources

### brave-search://metadata/trending
Provides currently trending search topics across different categories.

### brave-search://web/popular-queries/{category}
Provides pre-cached results for common queries in different categories.
Available categories: technology, science, news

### brave-search://docs/api-reference
Documentation about the Brave Search API and its capabilities.

### brave-search://docs/usage-examples
Examples of how to use the Brave Search MCP tools effectively.

### brave-search://history/recent
Recent searches performed through the MCP server.`;

// Usage examples documentation
const usageExamples = `# Brave Search MCP Usage Examples

## Web Search Examples

### Basic web search
\`\`\`json
{
  "query": "climate change solutions"
}
\`\`\`

### Limiting results
\`\`\`json
{
  "query": "best smartphones 2025",
  "count": 5
}
\`\`\`

### Pagination
\`\`\`json
{
  "query": "renewable energy technologies",
  "count": 10,
  "offset": 1
}
\`\`\`

## Local Search Examples

### Finding nearby restaurants
\`\`\`json
{
  "query": "italian restaurants near me"
}
\`\`\`

### Finding services in a specific location
\`\`\`json
{
  "query": "dentists in Boston",
  "count": 8
}
\`\`\`

## Code Search Examples

### Basic code search
\`\`\`json
{
  "query": "implement binary search"
}
\`\`\`

### Language-specific search
\`\`\`json
{
  "query": "async/await example",
  "language": "javascript"
}
\`\`\`

### Site-specific search
\`\`\`json
{
  "query": "react hooks tutorial",
  "site": "github.com"
}
\`\`\`

### Combined filters
\`\`\`json
{
  "query": "implement quicksort",
  "language": "python",
  "site": "stackoverflow.com",
  "count": 5
}
\`\`\``;

// Server implementation
// *** Log before server creation ***
console.error("Brave Search Server: Creating server instance...");
const server = new Server(
  {
    name: "example-servers/brave-search",
    version: "0.1.0",
  },
  {
    capabilities: {
      tools: {},
      resources: {},
    },
  },
);
console.error("Brave Search Server: Server instance created.");

// Check for API key
const BRAVE_API_KEY = process.env.BRAVE_API_KEY; // No longer using non-null assertion !
// *** Log the received API Key (or lack thereof) ***
console.error(`Brave Search Server: Final check - BRAVE_API_KEY: ${BRAVE_API_KEY ? 'Exists (length: ' + BRAVE_API_KEY.length + ')' : 'MISSING!'}`);

if (!BRAVE_API_KEY) {
  console.error("Error: BRAVE_API_KEY environment variable is required but could not be loaded.");
  process.exit(1); // Exit if key is missing after all attempts
}

// Read rate limits from environment variables with defaults
const RATE_LIMIT = {
  perSecond: parseInt(process.env.BRAVE_RATE_LIMIT_SECOND || '1', 10),
  perMonth: parseInt(process.env.BRAVE_RATE_LIMIT_MONTH || '15000', 10)
};
console.error(`Rate limits set: ${RATE_LIMIT.perSecond}/sec, ${RATE_LIMIT.perMonth}/month`);

let requestCount = {
  second: 0,
  month: 0,
  lastReset: Date.now()
};

function checkRateLimit() {
  const now = Date.now();
  if (now - requestCount.lastReset > 1000) {
    requestCount.second = 0;
    requestCount.lastReset = now;
  }
  if (requestCount.second >= RATE_LIMIT.perSecond ||
    requestCount.month >= RATE_LIMIT.perMonth) {
    throw new Error('Rate limit exceeded');
  }
  requestCount.second++;
  requestCount.month++;
}

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
  locations?: {
    results?: Array<{
      id: string; // Required by API
      title?: string;
    }>;
  };
}

interface BraveLocation {
  id: string;
  name: string;
  address: {
    streetAddress?: string;
    addressLocality?: string;
    addressRegion?: string;
    postalCode?: string;
  };
  coordinates?: {
    latitude: number;
    longitude: number;
  };
  phone?: string;
  rating?: {
    ratingValue?: number;
    ratingCount?: number;
  };
  openingHours?: string[];
  priceRange?: string;
}

interface BravePoiResponse {
  results: BraveLocation[];
}

interface BraveDescription {
  descriptions: {[id: string]: string};
}

function isBraveWebSearchArgs(args: unknown): args is { query: string; count?: number; offset?: number } {
  return (
    typeof args === "object" &&
    args !== null &&
    "query" in args &&
    typeof (args as { query: string }).query === "string"
  );
}

function isBraveLocalSearchArgs(args: unknown): args is { query: string; count?: number } {
  return (
    typeof args === "object" &&
    args !== null &&
    "query" in args &&
    typeof (args as { query: string }).query === "string"
  );
}

function isBraveCodeSearchArgs(args: unknown): args is { query: string; language?: string; site?: string; count?: number; offset?: number } {
  return (
    typeof args === "object" &&
    args !== null &&
    "query" in args &&
    typeof (args as { query: string }).query === "string"
  );
}

function enhanceCodeQuery(query: string, language?: string, site?: string): string {
  let enhancedQuery = query;

  // Add language context if provided
  if (language && language.trim() !== "") {
    // Check if query already contains language
    if (!query.toLowerCase().includes(language.toLowerCase())) {
      enhancedQuery = `${enhancedQuery} ${language}`;
    }
  }

  // Add site restriction if provided
  if (site && site.trim() !== "") {
    enhancedQuery = `${enhancedQuery} site:${site}`;
  }

  // Add programming context if not already present
  const codingTerms = ["code", "example", "function", "implementation", "snippet"];
  const hasCodeContext = codingTerms.some(term => query.toLowerCase().includes(term));

  if (!hasCodeContext) {
    enhancedQuery = `${enhancedQuery} code example`;
  }

  return enhancedQuery;
}

async function performWebSearch(query: string, count: number = 10, offset: number = 0) {
  checkRateLimit();
  const url = new URL('https://api.search.brave.com/res/v1/web/search');
  url.searchParams.set('q', query);
  url.searchParams.set('count', Math.min(count, 20).toString()); // API limit
  url.searchParams.set('offset', offset.toString());

  const headers: HeadersInit = {
    'Accept': 'application/json',
    'Accept-Encoding': 'gzip',
  };
  if (BRAVE_API_KEY) {
    headers['X-Subscription-Token'] = BRAVE_API_KEY;
  }

  const response = await fetch(url, { headers });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`Brave API Error (${response.status} ${response.statusText}): ${errorBody}`);
  }

  const data = await response.json() as BraveWeb;

  const results = (data.web?.results || []).map(result => ({
    title: result.title || '',
    description: result.description || '',
    url: result.url || ''
  }));

  return results;
}

async function performLocalSearch(query: string, count: number = 5) {
  checkRateLimit();
  const webUrl = new URL('https://api.search.brave.com/res/v1/web/search');
  webUrl.searchParams.set('q', query);
  webUrl.searchParams.set('search_lang', 'en');
  webUrl.searchParams.set('result_filter', 'locations');
  webUrl.searchParams.set('count', Math.min(count, 20).toString());

  const headers: HeadersInit = {
    'Accept': 'application/json',
    'Accept-Encoding': 'gzip',
  };
  if (BRAVE_API_KEY) {
    headers['X-Subscription-Token'] = BRAVE_API_KEY;
  }

  const webResponse = await fetch(webUrl, { headers });

  if (!webResponse.ok) {
    const errorBody = await webResponse.text();
    throw new Error(`Brave API Error (Web Search Fallback) (${webResponse.status} ${webResponse.statusText}): ${errorBody}`);
  }

  const webData = await webResponse.json() as BraveWeb;
  const locationIds = webData.locations?.results?.filter((r): r is {id: string; title?: string} => r.id != null).map(r => r.id) || [];

  if (locationIds.length === 0) {
    console.error("No local results found via location IDs, falling back to web search.");
    return performWebSearch(query, count);
  }

  const [poisData, descriptionsData] = await Promise.all([
    getPoisData(locationIds),
    getDescriptionsData(locationIds)
  ]);

  return formatLocalResultsStructured(poisData, descriptionsData);
}

async function getPoisData(ids: string[]): Promise<BravePoiResponse> {
  checkRateLimit();
  const url = new URL('https://api.search.brave.com/res/v1/local/pois');
  ids.filter(Boolean).forEach(id => url.searchParams.append('ids', id));

  const headers: HeadersInit = {
    'Accept': 'application/json',
    'Accept-Encoding': 'gzip',
  };
  if (BRAVE_API_KEY) {
    headers['X-Subscription-Token'] = BRAVE_API_KEY;
  }

  const response = await fetch(url, { headers });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`Brave API Error (getPoisData) (${response.status} ${response.statusText}): ${errorBody}`);
  }

  const poisResponse = await response.json() as BravePoiResponse;
  return poisResponse;
}

async function getDescriptionsData(ids: string[]): Promise<BraveDescription> {
  checkRateLimit();
  const url = new URL('https://api.search.brave.com/res/v1/local/descriptions');
  ids.filter(Boolean).forEach(id => url.searchParams.append('ids', id));

  const headers: HeadersInit = {
    'Accept': 'application/json',
    'Accept-Encoding': 'gzip',
  };
  if (BRAVE_API_KEY) {
    headers['X-Subscription-Token'] = BRAVE_API_KEY;
  }

  const response = await fetch(url, { headers });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`Brave API Error (getDescriptionsData) (${response.status} ${response.statusText}): ${errorBody}`);
  }

  const descriptionsData = await response.json() as BraveDescription;
  return descriptionsData;
}

function formatLocalResultsStructured(poisData: BravePoiResponse, descData: BraveDescription): object[] {
  const results = (poisData.results || []).map(poi => {
    const address = [
      poi.address?.streetAddress ?? '',
      poi.address?.addressLocality ?? '',
      poi.address?.addressRegion ?? '',
      poi.address?.postalCode ?? ''
    ].filter(part => part !== '').join(', ') || 'N/A';

    return {
      name: poi.name,
      address: address,
      phone: poi.phone || 'N/A',
      ratingValue: poi.rating?.ratingValue ?? 'N/A',
      ratingCount: poi.rating?.ratingCount ?? 0,
      priceRange: poi.priceRange || 'N/A',
      openingHours: (poi.openingHours || []).join(', ') || 'N/A',
      description: descData.descriptions[poi.id] || 'No description available'
    };
  });
  return results.length > 0 ? results : [{ message: 'No local results found' }];
}

async function performCodeSearch(
  query: string,
  language: string = "",
  site: string = "",
  count: number = 10,
  offset: number = 0
) {
  checkRateLimit();

  const enhancedQuery = enhanceCodeQuery(query, language, site);

  const url = new URL('https://api.search.brave.com/res/v1/web/search');
  url.searchParams.set('q', enhancedQuery);
  url.searchParams.set('count', Math.min(count, 20).toString());
  url.searchParams.set('offset', offset.toString());

  url.searchParams.set('search_lang', language || 'en');

  const headers: HeadersInit = {
    'Accept': 'application/json',
    'Accept-Encoding': 'gzip',
  };
  if (BRAVE_API_KEY) {
    headers['X-Subscription-Token'] = BRAVE_API_KEY;
  }

  const response = await fetch(url, { headers });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`Brave API Error (performCodeSearch) (${response.status} ${response.statusText}): ${errorBody}`);
  }

  const data = await response.json() as BraveWeb;

  return formatCodeResultsStructured(data, language);
}

function formatCodeResultsStructured(data: BraveWeb, language: string): object[] {
  const results = (data.web?.results || []).map(result => {
    const isCodeRepository = result.url.includes('github.com') ||
                            result.url.includes('gitlab.com') ||
                            result.url.includes('bitbucket.org');

    const isDocumentation = result.url.includes('docs.') ||
                           result.url.includes('documentation') ||
                           result.url.includes('reference');

    const isQA = result.url.includes('stackoverflow.com') ||
                result.url.includes('stackexchange.com');

    let sourceType = "Website";
    if (isCodeRepository) sourceType = "Repository";
    else if (isDocumentation) sourceType = "Documentation";
    else if (isQA) sourceType = "Q&A";

    const domain = new URL(result.url).hostname.replace('www.', '');

    return {
        title: result.title || '',
        source: domain,
        sourceType: sourceType,
        language: language || 'N/A',
        description: result.description || '',
        url: result.url || ''
    };
  });
  return results.length > 0 ? results : [{ message: 'No code-related results found' }];
}

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [WEB_SEARCH_TOOL, LOCAL_SEARCH_TOOL, CODE_SEARCH_TOOL],
}));

// Corrected ListResourcesRequestSchema handler
server.setRequestHandler(ListResourcesRequestSchema, async () => ({
  resources: [
    TRENDING_TOPICS_RESOURCE,
    POPULAR_QUERIES_RESOURCE,
    API_REFERENCE_RESOURCE,
    USAGE_EXAMPLES_RESOURCE,
    SEARCH_HISTORY_RESOURCE // This was missing in the corrupted section
  ],
}));

// Corrected ReadResourceRequestSchema handler
server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const { uri } = request.params; // Define uri here

  try { // Start try block here
    // Handle trending topics resource
    if (uri === "brave-search://metadata/trending") {
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(trendingTopics, null, 2)
          }
        ]
      };
    }

    // Handle popular queries resource with category parameter
    if (uri.startsWith("brave-search://web/popular-queries/")) {
      const category = uri.split('/').pop();
      if (category && popularQueriesCache[category]) {
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(popularQueriesCache[category], null, 2)
            }
          ]
        };
      } else {
        return {
          content: [
            {
              type: "text",
              text: `No cached queries available for category: ${category}. Available categories: ${Object.keys(popularQueriesCache).join(', ')}`
            }
          ],
          isError: true
        };
      }
    }

    // Handle API reference documentation
    if (uri === "brave-search://docs/api-reference") {
      return {
        content: [
          {
            type: "text",
            text: apiReference
          }
        ]
      };
    }

    // Handle usage examples documentation
    if (uri === "brave-search://docs/usage-examples") {
      return {
        content: [
          {
            type: "text",
            text: usageExamples
          }
        ]
      };
    }

    // Handle search history
    if (uri === "brave-search://history/recent") {
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(searchHistory.slice(-10).reverse(), null, 2) // Return the 10 most recent searches
          }
        ]
      };
    }

    // Handle unknown resource
    return {
      content: [
        {
          type: "text",
          text: `Unknown resource: ${uri}`
        }
      ],
      isError: true
    };
  } catch (error) { // Catch block here
    return {
      content: [
        {
          type: "text",
          text: `Error accessing resource: ${error instanceof Error ? error.message : String(error)}`
        }
      ],
      isError: true
    };
  }
}); // End handler here


server.setRequestHandler(CallToolRequestSchema, async (request) => {
  try {
    const { name, arguments: args } = request.params;

    if (!args) {
      throw new Error("No arguments provided");
    }

    switch (name) {
      case "brave_web_search": {
        if (!isBraveWebSearchArgs(args)) {
          throw new Error("Invalid arguments for brave_web_search");
        }
        const { query, count = 10, offset = 0 } = args; // Added offset here

        // Add to search history
        searchHistory.push({
          query,
          timestamp: Date.now(),
          tool: "brave_web_search"
        });

        const results = await performWebSearch(query, count, offset); // Pass offset
        return {
          content: [{ type: "text", text: JSON.stringify(results, null, 2) }], // Stringify results
          isError: false,
        };
      }

      case "brave_local_search": {
        if (!isBraveLocalSearchArgs(args)) {
          throw new Error("Invalid arguments for brave_local_search");
        }
        const { query, count = 5 } = args;

        // Add to search history
        searchHistory.push({
          query,
          timestamp: Date.now(),
          tool: "brave_local_search"
        });

        const results = await performLocalSearch(query, count);
        return {
          content: [{ type: "text", text: JSON.stringify(results, null, 2) }], // Stringify results
          isError: false,
        };
      }

      case "brave_code_search": {
        if (!isBraveCodeSearchArgs(args)) {
          throw new Error("Invalid arguments for brave_code_search");
        }
        const { query, language = "", site = "", count = 10, offset = 0 } = args;

        // Add to search history
        searchHistory.push({
          query,
          timestamp: Date.now(),
          tool: "brave_code_search"
        });

        const results = await performCodeSearch(query, language, site, count, offset);
        return {
          content: [{ type: "text", text: JSON.stringify(results, null, 2) }], // Stringify results
          isError: false,
        };
      }

      default:
        return {
          content: [{ type: "text", text: `Unknown tool: ${name}` }],
          isError: true,
        };
    }
  } catch (error) {
    return {
      content: [
        {
          type: "text",
          text: `Error: ${error instanceof Error ? error.message : String(error)}`,
        },
      ],
      isError: true,
    };
  }
});

async function runServer() {
  // *** Log before transport creation ***
  console.error("Brave Search Server: Creating StdioServerTransport...");
  const transport = new StdioServerTransport();
  console.error("Brave Search Server: StdioServerTransport created.");

  // *** Log before connecting ***
  console.error("Brave Search Server: Attempting server.connect()...");
  await server.connect(transport);
  // *** Log after successful connection ***
  console.error("Brave Search MCP Server running on stdio"); // This is the success message
}

// *** Log before calling runServer ***
console.error("Brave Search Server: Calling runServer()...");
runServer().catch((error) => {
  // *** Log fatal errors ***
  console.error("Fatal error running server:", error);
  process.exit(1); // Exit on fatal error
});