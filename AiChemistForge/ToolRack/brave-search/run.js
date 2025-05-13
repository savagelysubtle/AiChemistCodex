#!/usr/bin/env node

import { execSync } from 'child_process';
import fs from 'fs';
import path, { dirname } from 'path';
import { fileURLToPath } from 'url';

// Get the path to the index.js file
// In ES modules, __dirname is not available, so we create an equivalent
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const indexPath = path.join(__dirname, 'dist', 'index.js');

// Check if the file exists
if (!fs.existsSync(indexPath)) {
  console.error(`Error: Could not find ${indexPath}`);
  process.exit(1);
}

try {
  // Run the index.js file with dotenvx to load environment variables from .env.local
  console.log('Starting brave-search MCP server with dotenvx...');
  execSync(`dotenvx run -f .env.local -- node ${indexPath}`, {
    stdio: 'inherit',
    env: process.env
  });
} catch (error) {
  console.error('Error running brave-search MCP server:', error);
  process.exit(1);
}