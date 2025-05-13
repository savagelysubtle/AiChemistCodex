import { spawn } from "child_process";
import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import { spawnPromise } from "spawn-rx";
import {
  findSchemaFile,
  findServerEntryPoint,
  hasNodeJs,
  hasUvx,
  isNpmPackage, // ⬅️  NEW
  normalizeServerPath
} from "./utils.mjs"; // Import from utils

// Installation-related functions will be moved here

/**
 * Gets the full path to the virtual environment
 * @returns Path to .venv directory or null if not found
 */
export function getVenvPath(): string | null {
  // Start with the current directory
  const projectDir = process.cwd();
  const venvPath = path.join(projectDir, ".venv");

  if (fs.existsSync(venvPath)) {
    return venvPath.replace(/\//g, "\\");
  }

  // If we're in src directory, try one level up
  if (path.basename(projectDir) === "src") {
    const parentDir = path.dirname(projectDir);
    const parentVenvPath = path.join(parentDir, ".venv");

    if (fs.existsSync(parentVenvPath)) {
      return parentVenvPath.replace(/\//g, "\\");
    }
  }

  return null;
}

/**
 * Gets the local executable path within the project's .venv/Scripts directory
 * @param execName Name of the executable (e.g., "uv.exe", "node.exe", "npm.cmd")
 * @returns Full Windows path to the executable or null if not found
 */
export function getLocalExePath(execName: string): string | null {
  const venvPath = getVenvPath();
  if (!venvPath) return null;

  const execPath = path.join(venvPath, "Scripts", execName);

  // Ensure Windows path format with double backslashes
  const normalizedPath = execPath.replace(/\//g, "\\");

  if (fs.existsSync(normalizedPath)) {
    return normalizedPath;
  }

  return null;
}

/**
 * Gets the local uv.exe path
 * @returns Full Windows path to uv.exe or null if not found
 */
export function getLocalUvPath(): string | null {
  return getLocalExePath("uv.exe");
}

/**
 * Gets the local node.exe path
 * @returns Full Windows path to node.exe or null if not found
 */
export function getLocalNodePath(): string | null {
  return getLocalExePath("node.exe");
}

/**
 * Gets the local npm.cmd path
 * @returns Full Windows path to npm.cmd or null if not found
 */
export function getLocalNpmPath(): string | null {
  // Check for npm.cmd first (Windows)
  const npmCmd = getLocalExePath("npm.cmd");
  if (npmCmd) return npmCmd;

  // Fallback to npm (non-Windows)
  return getLocalExePath("npm");
}

/**
 * Identifies the category of a tool based on its name
 * @param name The name of the tool/package
 * @returns The category: "ToolRack", "Compendium", or "Brain"
 */
export function identifyToolCategory(name: string): "ToolRack" | "Compendium" | "Brain" {
  // Determine the category based on the name or package contents
  const lowerName = name.toLowerCase();

  if (
    lowerName.includes("obsidian") ||
    lowerName.includes("vault") ||
    lowerName.includes("doc") ||
    lowerName.includes("note") ||
    lowerName.includes("compendium")
  ) {
    return "Compendium";
  }

  if (
    lowerName.includes("memory") ||
    lowerName.includes("brain") ||
    lowerName.includes("mem") ||
    lowerName.includes("knowledge") ||
    lowerName.includes("mind")
  ) {
    return "Brain";
  }

  // Default case
  return "ToolRack";
}

/**
 * Gets the storage path for a specific tool category
 * @param toolName The name of the tool
 * @returns The full path where the tool should be stored
 */
export function getToolPath(toolName: string): string {
  const baseDir = process.env.TOOL_SHED_PATH || "D:\\Coding\\TheToolShed";
  const category = identifyToolCategory(toolName);
  return path.join(baseDir, category);
}

/**
 * Clones a git repository to the appropriate category directory
 * @param gitUrl The URL of the git repository
 * @returns Path to the cloned repository
 */
export async function cloneGitRepo(gitUrl: string): Promise<string> {
  // Extract repo name from URL for categorization
  const repoName =
    gitUrl
      .split("/")
      .pop()
      ?.replace(/\.git$/, "") || "";

  // Get only the category directory without appending the repo name
  const categoryDir = getToolPath(repoName);

  // Create category directory if it doesn't exist
  if (!fs.existsSync(categoryDir)) {
    fs.mkdirSync(categoryDir, { recursive: true });
  }

  // The full path where the repo will be after cloning
  const repoPath = path.join(categoryDir, repoName);

  return new Promise<string>((resolve, reject) => {
    // If repo exists, pull latest changes
    if (fs.existsSync(repoPath)) {
      console.log(`Repository already exists at ${repoPath}, pulling latest changes`);
      const git = spawn("git", ["pull"], { cwd: repoPath });

      git.on("close", (code) => {
        if (code === 0) {
          resolve(repoPath);
        } else {
          reject(new Error(`Git pull failed with code ${code}`));
        }
      });

      git.stderr.on("data", (data) => {
        console.error(`Git stderr: ${data}`);
      });
    } else {
      // Clone directly to the category directory - git will create the repo directory
      console.log(`Cloning repository to ${categoryDir}`);
      const git = spawn("git", ["clone", gitUrl], { cwd: categoryDir });

      git.on("close", (code) => {
        if (code === 0) {
          resolve(repoPath);
        } else {
          reject(new Error(`Git clone failed with code ${code}`));
        }
      });

      git.stderr.on("data", (data) => {
        console.error(`Git stderr: ${data}`);
      });
    }
  });
}

interface CursorToolConfig {
  name: string;
  cmd: string;
  args: string[];
  env?: Record<string, string>;
}

interface CursorConfig {
  tools: CursorToolConfig[];
  mcpServers?: Record<string, any>; // Keep existing mcpServers property if it exists
}

/**
 * Install a server into Cursor's config following Windows formatting conventions
 * @param name Display name for the MCP server in Cursor
 * @param cmd Command to execute (e.g., node, npx, python)
 * @param args Arguments to pass to the command
 * @param env Environment variables to set, delimited by =
 * @returns The configuration object or true if successful
 */
export function installToCursor(name: string, cmd: string, args: string[], env?: string[]) {
  const configPath = process.env.CURSOR_MCP_CONFIG
    ?? path.join(os.homedir(), ".cursor", "mcp.json");

  const cfgDir = path.dirname(configPath);
  fs.mkdirSync(cfgDir, { recursive: true });

  let cfg: CursorConfig;
  try {
    cfg = fs.existsSync(configPath)
      ? JSON.parse(fs.readFileSync(configPath, "utf8")) as CursorConfig
      : { tools: [] };
  } catch (e) {
    console.error("Failed to parse existing Cursor config, creating new one:", e);
    cfg = { tools: [] };
  }


  // Ensure tools is an array
  if (!Array.isArray(cfg.tools)) {
      cfg.tools = [];
  }

  // De‑dupe by name
  cfg.tools = cfg.tools.filter(t => t.name !== name);

  const newTool: CursorToolConfig = { name, cmd, args };
  if (env && env.length > 0) {
      newTool.env = env.reduce((acc: Record<string, string>, val) => {
          const [key, value] = val.split("=");
          if (key) acc[key] = value || "";
          return acc;
      }, {});
  }

  cfg.tools.push(newTool);
  fs.writeFileSync(configPath, JSON.stringify(cfg, null, 2));
}

/**
 * Installs an NPM or UVX package to Cursor
 * @param name Package name
 * @param npmIfTrueElseUvx Whether to use NPM (true) or UVX (false)
 * @param args Additional arguments
 * @param env Environment variables
 * @returns The installed configuration
 */
export function installRepoWithArgsToCursor(
  name: string,
  npmIfTrueElseUvx: boolean,
  args?: string[],
  env?: string[],
) {
  // If the name is in a scoped package, we need to remove the scope
  const serverName = /^@.*\//i.test(name) ? name.split("/")[1] : name;

  // For Cursor, create a friendly display name
  const formattedName = serverName.replace(/-/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());

  // Check if we're using a package that requires special handling
  if (name === "mcp-openapi-schema" || name.includes("openapi-schema")) {
    // For OpenAPI schema servers, find schema file anywhere in the arguments
    const schemaFile = findSchemaFile(args);

    if (schemaFile) {
      // Special configuration for OpenAPI schema servers
      // First try to get the installed package path
      try {
        const packagePath = path.dirname(require.resolve(`${name}/package.json`));
        const indexPath = path.join(packagePath, "index.mjs");

        if (fs.existsSync(indexPath)) {
          // Create new args array with normalized schema path
          const newArgs =
            args?.map((arg) => {
              if (arg === schemaFile) {
                try {
                  return normalizeServerPath(schemaFile, process.cwd());
                } catch (e) {
                  return arg;
                }
              }
              return arg;
            }) ?? [];

          return installToCursor(formattedName, "node", [indexPath, ...newArgs], env);
        }
      } catch (error) {
        console.warn(`Couldn't resolve ${name} package path, falling back to npx`);
      }
    }
  }

  // Modify to use local paths when available
  const localNpmPath = getLocalNpmPath();

  // For X Twitter MCP specifically and other Python packages
  if (name.includes("x-mcp") ||
      name.includes("python") ||
      name.endsWith(".py") ||
      !npmIfTrueElseUvx) {
    // For Python MCP servers, we should use python -m module_name pattern instead of uvx
    // This helps ensure proper module paths and environment

    const moduleName = name.replace(/-/g, "_").replace(/\.git$/, "");
    // Extract module name from common patterns like username/repo-name.git
    const cleanModuleName = moduleName.includes("/")
      ? moduleName
          .split("/")
          .pop()!
          .replace(/\.git$/, "")
      : moduleName;

    // For X Twitter MCP specifically
    if (name.includes("x-mcp")) {
      return installToCursor(
        "X Twitter Tools",
        "python",
        ["-m", `${cleanModuleName.replace(/-/g, "_")}.server`],
        env,
      );
    }

    // For other Python-based MCP servers
    return installToCursor(formattedName, "python", ["-m", cleanModuleName], env);
  } else {
    // For npm packages, use local npm.cmd if available
    const npmCommand = localNpmPath ? localNpmPath : "npx";
    return installToCursor(
      formattedName,
      npmCommand,
      ["-y", name, ...(args ?? [])],
      env
    );
  }
}

/**
 * Attempts to install Node.js dependencies and find server entry points
 * @param directory The directory containing the Node.js project
 * @returns Record of entry point names and paths
 */
export async function attemptNodeInstall(directory: string): Promise<Record<string, string>> {
  // Use local npm if available
  const localNpmPath = getLocalNpmPath();
  const npmCommand = localNpmPath || "npm";

  await spawnPromise(npmCommand, ["install"], { cwd: directory });

  // Run down package.json looking for bins
  const pkg = JSON.parse(fs.readFileSync(path.join(directory, "package.json"), "utf-8"));

  const result: Record<string, string> = {};

  // Check for bin entries first
  if (pkg.bin) {
    Object.keys(pkg.bin).forEach((key) => {
      result[key] = normalizeServerPath(pkg.bin[key], directory);
    });
  }

  // If no bins, try main entry point
  if (Object.keys(result).length === 0 && pkg.main) {
    result[pkg.name] = normalizeServerPath(pkg.main, directory);
  }

  // If still no results, try to find a server entry point
  if (Object.keys(result).length === 0) {
    const entryPoint = findServerEntryPoint(directory);
    if (entryPoint) {
      result[pkg.name || "server"] = entryPoint.path;
    }
  }

  return result;
}

/**
 * Adds an MCP server to Cursor's configuration
 * @param name Display name for the server
 * @param command Command to execute
 * @param args Arguments to pass
 * @param serverPath Path to the server script
 * @param env Environment variables
 * @returns Response object with content and potential error flag
 */
export async function addToCursorConfig(
  name: string,
  command?: string,
  args?: string[],
  serverPath?: string,
  env?: string[],
) {
  const isInContainer = process.env.SMITHERY_CONTAINER === "true";

  // Handle the case where the user provides either a command or a path
  if (!serverPath && !command) {
    return {
      content: [
        {
          type: "text",
          text: "Error: You must provide either a command or a path!",
        },
      ],
      isError: true,
    };
  }

  try {
    // If a server path is provided, use that instead of the command+args
    if (serverPath) {
      // Normalize the server path with explicit Windows path formatting
      const normalizedPath = normalizeServerPath(serverPath, process.cwd());

      if (!isInContainer && !fs.existsSync(normalizedPath)) {
        return {
          content: [
            {
              type: "text",
              text: `Error: Path ${normalizedPath} does not exist!`,
            },
          ],
          isError: true,
        };
      }

      // Use node to run the server if it's a JavaScript file
      if (normalizedPath.endsWith(".js") || normalizedPath.endsWith(".mjs")) {
        command = "node";
        args = [normalizedPath, ...(args || [])];
      } else if (normalizedPath.endsWith(".py")) {
        // Use python for Python files
        command = "python";
        args = [normalizedPath, ...(args || [])];
      } else {
        // Otherwise use the serverPath as the command
        command = normalizedPath;
        args = args || [];
      }
    } else if (args) {
      // If we have command and args, normalize any file paths in args
      args = args.map((arg) => {
        // Only normalize if it looks like a file path and not an npm package
        if (arg &&
            typeof arg === "string" &&
            (arg.includes("/") || arg.includes("\\")) &&
            !arg.startsWith("@") &&
            !arg.includes("-y")) {
          try {
            return normalizeServerPath(arg, process.cwd());
          } catch (e) {
            // If normalization fails, return the original arg
            return arg;
          }
        }
        return arg;
      });
    }

    // Create server config
    const envObj = (env ?? []).reduce(
      (acc: Record<string, string>, val) => {
        const [key, value] = val.split("=");
        if (key) acc[key] = value || "";
        return acc;
      },
      {} as Record<string, string>,
    );

    const serverConfig = {
      command: command!, // We've verified either command or serverPath is provided
      type: "stdio",
      args: args || [],
      ...(env && env.length > 0 ? { env: envObj } : {}),
    };

    if (isInContainer) {
      // In Smithery, just return the configuration
      const config: { mcpServers: Record<string, any> } = { mcpServers: {} };
      config.mcpServers[name] = serverConfig;

      return {
        content: [
          {
            type: "text",
            text:
              `Here's the configuration to add to your ~/.cursor/mcp.json file:\n\n` +
              `\`\`\`json\n${JSON.stringify(config, null, 2)}\n\`\`\`\n\n` +
              `After adding this configuration, restart Cursor to apply the changes.`,
          },
        ],
      };
    } else {
      // In local environment, update the config file
      const configPath = path.join(os.homedir(), ".cursor", "mcp.json");

      let config: { mcpServers: Record<string, any> };
      try {
        config = fs.existsSync(configPath)
          ? JSON.parse(fs.readFileSync(configPath, "utf8"))
          : { mcpServers: {} };
      } catch (e) {
        config = { mcpServers: {} };
      }

      config.mcpServers = config.mcpServers || {};
      config.mcpServers[name] = serverConfig;

      fs.writeFileSync(configPath, JSON.stringify(config, null, 2));

      return {
        content: [
          {
            type: "text",
            text: `Successfully added ${name} to your Cursor configuration! Please restart Cursor to apply the changes.`,
          },
        ],
      };
    }
  } catch (e) {
    return {
      content: [
        {
          type: "text",
          text: `Error: ${e}`,
        },
      ],
      isError: true,
    };
  }
}

/**
 * Installs an MCP server from a local directory
 * @param dirPath Path to the local directory
 * @param args Additional arguments
 * @param env Environment variables
 * @returns Response object with content and potential error flag
 */
export async function installLocalMcpServer(dirPath: string, args?: string[], env?: string[]) {
  const isInContainer = process.env.SMITHERY_CONTAINER === "true";

  if (isInContainer) {
    return {
      content: [
        {
          type: "text",
          text:
            "Local directory installation is not available in the Smithery environment. " +
            "Please use this tool locally with Cursor to install from local directories.",
        },
      ],
      isError: true,
    };
  }

  try {
    // Normalize the directory path and ensure Windows path format
    const normalizedDirPath = normalizeServerPath(dirPath, process.cwd());

    if (!fs.existsSync(normalizedDirPath)) {
      return {
        content: [
          {
            type: "text",
            text: `Path ${normalizedDirPath} does not exist locally!`,
          },
        ],
        isError: true,
      };
    }

    // Check if it's a Node.js package with package.json
    if (fs.existsSync(path.join(normalizedDirPath, "package.json"))) {
      const servers = await attemptNodeInstall(normalizedDirPath);

      if (Object.keys(servers).length > 0) {
        Object.keys(servers).forEach((name) => {
          // Install to Cursor with proper formatting
          const formattedName = name.replace(/-/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());

          // Ensure server paths are properly Windows-formatted
          const serverPath = servers[name].replace(/\//g, '\\');
          installToCursor(formattedName, "node", [serverPath, ...(args ?? [])], env);
        });

        return {
          content: [
            {
              type: "text",
              text: `Installed the following servers to Cursor: ${Object.keys(servers).join(
                ", ",
              )}. Please restart Cursor to apply the changes.`,
            },
          ],
        };
      }
    }

    // If not a Node.js package or no server found, try to find a server entry point
    const entryPoint = findServerEntryPoint(normalizedDirPath);
    if (entryPoint) {
      // Get the directory name for a default name
      const dirName = path.basename(normalizedDirPath);
      const formattedName = dirName.replace(/-/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());

      // Ensure entryPoint path is properly Windows-formatted
      const serverPath = entryPoint.path.replace(/\//g, '\\');
      installToCursor(formattedName, entryPoint.command, [serverPath, ...(args ?? [])], env);

      return {
        content: [
          {
            type: "text",
            text: `Installed ${formattedName} to Cursor. Please restart Cursor to apply the changes.`,
          },
        ],
      };
    }

    return {
      content: [
        {
          type: "text",
          text: `Can't figure out how to install ${normalizedDirPath}. No server entry point was found.`,
        },
      ],
      isError: true,
    };
  } catch (e) {
    return {
      content: [
        {
          type: "text",
          text: `Error installing from local directory: ${e}`,
        },
      ],
      isError: true,
    };
  }
}

/**
 * Installs an MCP server from an npm or uvx package
 * @param name Package name
 * @param args Additional arguments
 * @param env Environment variables
 * @returns Response object with content and potential error flag
 */
export async function installRepoMcpServer(name: string, args?: string[], env?: string[]) {
  // Check for local Node.js first, then global
  const localNodePath = getLocalNodePath();

  if (!localNodePath && !(await hasNodeJs())) {
    return {
      content: [
        {
          type: "text",
          text: "Error: Node.js is not installed or found in .venv/Scripts, please install it!",
        },
      ],
      isError: true,
    };
  }

  const isNpm = await isNpmPackage(name);
  const hasUv = await hasUvx();
  const localUvPath = getLocalUvPath();

  if (!isNpm && !hasUv && !localUvPath) {
    return {
      content: [
        {
          type: "text",
          text: "Error: Package not found in npm registry and uv is not installed or found in .venv/Scripts!",
        },
      ],
      isError: true,
    };
  }

  const isInContainer = process.env.SMITHERY_CONTAINER === "true";

  try {
    if (isInContainer) {
      // In Smithery, we can't directly install - provide instructions instead
      const packageManager = isNpm ? "npm" : (localUvPath ? "uv" : "uvx");
      const configResult = installRepoWithArgsToCursor(name, isNpm, args, env);

      return {
        content: [
          {
            type: "text",
            text:
              `Instructions for installing ${name}:\n\n` +
              `1. Install the package with: ${packageManager} install -g ${name}\n\n` +
              `2. Add the following to your ~/.cursor/mcp.json file:\n\n` +
              `\`\`\`json\n${JSON.stringify(configResult, null, 2)}\n\`\`\`\n\n` +
              `3. Restart Cursor and the MCP server will be available`,
          },
        ],
      };
    } else {
      // Normal direct installation with proper categorization
      // If we have a local uv.exe, use that instead of relying on global uvx
      const useLocalUv = !isNpm && localUvPath;

      // Instead of storing in a variable, call the function directly
      if (useLocalUv) {
        installRepoWithLocalUv(name, localUvPath, args, env);
      } else {
        installRepoWithArgsToCursor(name, isNpm, args, env);
      }

      return {
        content: [
          {
            type: "text",
            text: `Successfully installed the ${name} MCP server!`,
          },
        ],
      };
    }
  } catch (e) {
    return {
      content: [
        {
          type: "text",
          text: `Error: ${e}`,
        },
      ],
      isError: true,
    };
  }
}

/**
 * Installs a package using the local uv.exe
 * @param name Package name
 * @param uvPath Full path to uv.exe
 * @param args Additional arguments
 * @param env Environment variables
 * @returns The configuration object
 */
export function installRepoWithLocalUv(
  name: string,
  uvPath: string,
  args?: string[],
  env?: string[]
): any {
  // If the name is in a scoped package, we need to remove the scope
  const serverName = /^@.*\//i.test(name) ? name.split("/")[1] : name;

  // For Cursor, create a friendly display name
  const formattedName = serverName.replace(/-/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());

  // For Python MCP servers
  if (name.includes("x-mcp") || name.includes("python") || name.endsWith(".py")) {
    const moduleName = name.replace(/-/g, "_").replace(/\.git$/, "");
    const cleanModuleName = moduleName.includes("/")
      ? moduleName.split("/").pop()!.replace(/\.git$/, "")
      : moduleName;

    // For X Twitter MCP specifically
    if (name.includes("x-mcp")) {
      return installToCursor(
        "X Twitter Tools",
        "python",
        ["-m", `${cleanModuleName.replace(/-/g, "_")}.server`],
        env,
      );
    }

    // For other Python-based MCP servers
    return installToCursor(formattedName, "python", ["-m", cleanModuleName], env);
  }

  // Use the full path to uv.exe
  return installToCursor(formattedName, uvPath, ["-y", name, ...(args ?? [])], env);
}

/**
 * Installs an MCP server from a git repository
 * @param gitUrl Git repository URL
 * @param args Additional arguments
 * @param env Environment variables
 * @returns Response object with content and potential error flag
 */
export async function installGitMcpServer(gitUrl: string, args?: string[], env?: string[]) {
  try {
    // Clone the repository to the appropriate directory based on its type
    const repoPath = await cloneGitRepo(gitUrl);

    // Use the existing local installation logic
    return await installLocalMcpServer(repoPath, args, env);
  } catch (e) {
    return {
      content: [
        {
          type: "text",
          text: `Error cloning or installing from git: ${e}`,
        },
      ],
      isError: true,
    };
  }
}
