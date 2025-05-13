import * as fs from "fs";
import * as path from "path";
import { spawnPromise } from "spawn-rx";

/**
 * Walks up the directory tree until it finds a folder that
 * looks like an MCP‑servers project.  If none is found, returns null.
 *
 * A folder is considered an MCP project when it contains either:
 *   –  an `mcp-server.json` marker **or**
 *   –  a `servers/` directory (created by this installer)
 */
export function findMcpProjectRoot(startDir: string = process.cwd()): string | null {
  let dir = path.resolve(startDir);
  const { root } = path.parse(dir);

  while (true) {
    const hasMarker = fs.existsSync(path.join(dir, "mcp-server.json"));
    const hasServersDir = fs.existsSync(path.join(dir, "servers"));
    if (hasMarker || hasServersDir) return dir;

    if (dir === root) return null; // hit the FS root – nothing found
    dir = path.dirname(dir);
  }
}

/**
 * Checks if Node.js is installed by attempting to get its version
 * @returns Promise<boolean> True if Node.js is installed and accessible
 */
export async function hasNodeJs(): Promise<boolean> {
  try {
    await spawnPromise("node", ["--version"]);
    return true;
  } catch (e) {
    return false;
  }
}

/**
 * Checks if UVX package manager is installed
 * @returns Promise<boolean> True if UVX is installed and accessible
 */
export async function hasUvx(): Promise<boolean> {
  try {
    await spawnPromise("uvx", ["--version"]);
    return true;
  } catch (e) {
    return false;
  }
}

/**
 * Checks if a given name corresponds to an npm package
 * @param name The package name to check
 * @returns Promise<boolean> True if the package exists in the npm registry
 */
export async function isNpmPackage(name: string): Promise<boolean> {
  try {
    await spawnPromise("npm", ["view", name, "version"]);
    return true;
  } catch (e) {
    return false;
  }
}

/**
 * Normalizes a file path to use proper system-specific separators and converts relative paths to absolute
 * @param filePath The file path to normalize
 * @param cwd Optional current working directory for resolving relative paths
 * @returns string The normalized absolute path with proper Windows-style backslashes
 * @throws Error if the path cannot be normalized or is invalid
 */
export function normalizeServerPath(filePath: string, cwd?: string): string {
  try {
    // Handle relative paths
    const absolutePath = path.isAbsolute(filePath)
      ? filePath
      : path.resolve(cwd || process.cwd(), filePath);

    // Normalize separators for the current OS
    const normalizedPath = path.normalize(absolutePath);

    // Ensure Windows-style path format with backslashes for display in config
    return normalizedPath.replace(/\//g, '\\');
  } catch (e) {
    throw new Error(`Failed to normalize path ${filePath}: ${e}`);
  }
}

/**
 * Searches for a schema file in the provided arguments
 * @param args Optional array of arguments to search through
 * @returns string | undefined Path to the schema file if found, undefined otherwise
 */
export function findSchemaFile(args?: string[]): string | undefined {
  if (!args) return undefined;
  return args.find(arg =>
    arg.endsWith('.yaml') ||
    arg.endsWith('.yml') ||
    arg.endsWith('.json') ||
    arg.endsWith('.openapi')
  );
}

/**
 * Looks for common server entry point files in a specified directory
 * @param dirPath The directory to search in
 * @returns Object containing the path and command if a server entry point is found
 */
export function findServerEntryPoint(dirPath: string): { path: string, command: string } | undefined {
  const commonEntryPoints = [
    { file: 'server.py', command: 'python' },
    { file: 'server.js', command: 'node' },
    { file: 'server.mjs', command: 'node' },
    { file: 'index.js', command: 'node' },
    { file: 'index.mjs', command: 'node' },
    { file: 'main.py', command: 'python' }
  ];

  for (const entry of commonEntryPoints) {
    const fullPath = path.join(dirPath, entry.file);
    if (fs.existsSync(fullPath)) {
      return {
        path: normalizeServerPath(fullPath),
        command: entry.command
      };
    }
  }

  return undefined;
}
