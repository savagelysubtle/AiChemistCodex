// src/logger.ts
const log = (level: 'info' | 'error' | 'warn' | 'debug', message: string, ...args: any[]) => {
  const timestamp = new Date().toISOString();
  // Force all log output to stderr to keep stdout clean for MCP JSON-RPC messages
  // const logMethod = level === 'error' ? console.error : level === 'warn' ? console.warn : console.log; // Old way
  const formattedMessage = `[${timestamp}] [${level.toUpperCase()}] ${message} ${args.map(arg => typeof arg === 'object' ? JSON.stringify(arg) : arg).join(' ')}\n`;
  process.stderr.write(formattedMessage);
};

export { log }; // Export the function