import { ErrorCode, McpError } from "@modelcontextprotocol/sdk/types.js";
import { exec } from 'child_process';
import { promises as fsPromises } from 'fs'; // Import fs.promises
import os from 'os';
import path from 'path';
import { promisify } from 'util';
import { WindowsProtectedPaths, WindowsSecurityConfig } from '../types/config.js';

const execAsync = promisify(exec);

// Cache for system resource usage
let cachedResourceUsage: { cpuPercent: number; memoryUsage: number } | null = null;
let lastResourceCheckTime: number = 0;
const RESOURCE_CACHE_DURATION_MS = 5000; // 5 seconds

// Cache for expanded protected paths
let expandedProtectedPathsCache: Record<string, string[]> | null = null;

// Default protected Windows paths
export const DEFAULT_PROTECTED_PATHS: WindowsProtectedPaths = {
  system: [
    'C:\\Windows',
    'C:\\Windows\\System32',
    'C:\\Windows\\SysWOW64',
  ],
  program: [
    'C:\\Program Files',
    'C:\\Program Files (x86)',
  ],
  user: [
    '%USERPROFILE%\\AppData',
    '%USERPROFILE%\\Documents',
    '%LOCALAPPDATA%',
    '%APPDATA%',
  ],
  registry: [
    'HKEY_LOCAL_MACHINE\\SOFTWARE',
    'HKEY_LOCAL_MACHINE\\SYSTEM',
    'HKEY_CLASSES_ROOT',
  ]
};

export async function isAdminRequired(command: string): Promise<boolean> {
  const elevationTriggers = [
    'runas',
    'net user',
    'net localgroup',
    'reg add HKEY_LOCAL_MACHINE',
    'reg delete HKEY_LOCAL_MACHINE',
    'sc ',
    'bcdedit',
    'diskpart',
    'DISM',
    'sfc ',
  ];

  return elevationTriggers.some(trigger => command.toLowerCase().includes(trigger.toLowerCase()));
}

// Function to pre-process and cache protected paths
function getExpandedProtectedPaths(protectedPathsConfig: WindowsProtectedPaths): Record<string, string[]> {
  if (expandedProtectedPathsCache) {
    return expandedProtectedPathsCache;
  }
  const expandedPaths: Record<string, string[]> = {};
  for (const [category, paths] of Object.entries(protectedPathsConfig)) {
    expandedPaths[category] = (paths as string[]).map(p => expandEnvironmentVars(p.toLowerCase()));
  }
  expandedProtectedPathsCache = expandedPaths;
  // Optionally add a mechanism to invalidate this cache if config can change dynamically
  return expandedPaths;
}


export async function validateWindowsPath(filePath: string, config: WindowsSecurityConfig): Promise<void> {
  const normalizedPath = path.normalize(filePath).toLowerCase();
  const expandedPath = expandEnvironmentVars(normalizedPath);

  // Get pre-processed protected paths
  const expandedProtectedPaths = getExpandedProtectedPaths(config.protectedPaths);

  // Check against protected paths
  for (const [category, paths] of Object.entries(expandedProtectedPaths)) {
    for (const expandedProtectedPath of paths) {
      // Ensure the protected path ends with a separator if it's a directory
      // to prevent partial matches (e.g., C:\Program Files (x86) matching C:\Program Files)
      const protectedDir = expandedProtectedPath.endsWith(path.sep) ? expandedProtectedPath : expandedProtectedPath + path.sep;
      const fileDir = expandedPath.endsWith(path.sep) ? expandedPath : expandedPath + path.sep;

      if (fileDir.startsWith(protectedDir)) {
        // Find the original path string for the error message
        const originalPath = (config.protectedPaths[category as keyof WindowsProtectedPaths] as string[])
                             .find(p => expandEnvironmentVars(p.toLowerCase()) === expandedProtectedPath) || expandedProtectedPath;
        throw new McpError(
          ErrorCode.InvalidRequest,
          `Access to ${category} path "${originalPath}" is restricted`
        );
      }
    }
  }

  // Check file size if it's a write operation (using async stat)
  if (config.resourceLimits?.maxFileSize) {
    try {
      const stats = await fsPromises.stat(expandedPath);
      if (stats.isFile() && stats.size > config.resourceLimits.maxFileSize) {
        throw new McpError(
          ErrorCode.InvalidRequest,
          `File size exceeds maximum allowed size of ${config.resourceLimits.maxFileSize} bytes`
        );
      }
    } catch (error: any) {
      // Ignore if file doesn't exist (ENOENT) or other access errors during check
      if (error.code !== 'ENOENT') {
         console.warn(`Could not check file size for ${expandedPath}: ${error.message}`);
      }
    }
  }
}

export function validateWindowsCommand(command: string, config: WindowsSecurityConfig): void {
  // Check for registry access
  if (!config.allowRegistryAccess && (command.includes('reg ') || command.includes('regedit'))) {
    throw new McpError(
      ErrorCode.InvalidRequest,
      'Registry access is disabled in the current configuration'
    );
  }

  // Check for PowerShell scripts
  if (!config.allowPowerShellScripts && command.toLowerCase().includes('.ps1')) {
    throw new McpError(
      ErrorCode.InvalidRequest,
      'PowerShell script execution is disabled in the current configuration'
    );
  }

  // Check for batch scripts
  if (!config.allowBatchScripts && (command.toLowerCase().includes('.bat') || command.toLowerCase().includes('.cmd'))) {
    throw new McpError(
      ErrorCode.InvalidRequest,
      'Batch script execution is disabled in the current configuration'
    );
  }

  // Check for system commands
  if (!config.allowSystemCommands) {
    const systemCommands = ['taskkill', 'tasklist', 'sc', 'net', 'netsh', 'wmic'];
    if (systemCommands.some(cmd => command.toLowerCase().startsWith(cmd + ' '))) {
      throw new McpError(
        ErrorCode.InvalidRequest,
        'System commands are disabled in the current configuration'
      );
    }
  }

  // Network restrictions
  if (config.networkRestrictions) {
    const networkCommands = ['curl', 'wget', 'netstat', 'ping', 'tracert', 'nslookup'];
    if (!config.networkRestrictions.allowOutbound &&
        networkCommands.some(cmd => command.toLowerCase().includes(cmd))) {
      throw new McpError(
        ErrorCode.InvalidRequest,
        'Network commands are disabled in the current configuration'
      );
    }

    // Check for blocked ports in network commands
    const portPattern = /:\d{1,5}/g;
    const ports = command.match(portPattern);
    if (ports) {
      const blockedPorts = config.networkRestrictions.blockedPorts || [];
      for (const portMatch of ports) {
        const port = parseInt(portMatch.substring(1));
        if (blockedPorts.includes(port)) {
          throw new McpError(
            ErrorCode.InvalidRequest,
            `Access to port ${port} is blocked`
          );
        }
      }
    }
  }
}

function expandEnvironmentVars(path: string): string {
  return path.replace(/%([^%]+)%/g, (_, variable) => {
    return process.env[variable] || `%${variable}%`;
  });
}

export async function validateWindowsSecurity(
  command: string,
  workingDir: string,
  config: WindowsSecurityConfig
): Promise<void> {
  // Validate working directory (now async)
  await validateWindowsPath(workingDir, config);

  // Validate command
  validateWindowsCommand(command, config);

  // Check for admin requirements
  if (config.requireAdminWarning && await isAdminRequired(command)) {
    throw new McpError(
      ErrorCode.InvalidRequest,
      'This command requires administrative privileges. Please check your security settings.'
    );
  }

  // Check system resource usage
  if (config.resourceLimits) {
    const { cpuPercent, memoryUsage } = await getSystemResourceUsage();

    if (cpuPercent > config.resourceLimits.maxCPUPercent) {
      throw new McpError(
        ErrorCode.InvalidRequest,
        `System CPU usage (${cpuPercent}%) exceeds maximum allowed (${config.resourceLimits.maxCPUPercent}%)`
      );
    }

    if (memoryUsage > config.resourceLimits.maxMemoryMB) {
      throw new McpError(
        ErrorCode.InvalidRequest,
        `System memory usage (${memoryUsage}MB) exceeds maximum allowed (${config.resourceLimits.maxMemoryMB}MB)`
      );
    }
  }
}

async function getSystemResourceUsage(): Promise<{ cpuPercent: number; memoryUsage: number }> {
  const now = Date.now();

  // Check cache first
  if (cachedResourceUsage && (now - lastResourceCheckTime < RESOURCE_CACHE_DURATION_MS)) {
    return cachedResourceUsage;
  }

  try {
    // Fetch new data
    const { stdout: wmic } = await execAsync('wmic cpu get loadpercentage');
    const cpuPercent = parseInt(wmic.split('\n')[1]) || 0;

    const totalMem = os.totalmem();
    const freeMem = os.freemem();
    const memoryUsage = Math.round((totalMem - freeMem) / (1024 * 1024)); // Convert to MB

    // Update cache
    cachedResourceUsage = { cpuPercent, memoryUsage };
    lastResourceCheckTime = now;

    return cachedResourceUsage;
  } catch (error) {
    console.error('Failed to get system resource usage:', error);
    // Return last known value if available, otherwise default
    return cachedResourceUsage || { cpuPercent: 0, memoryUsage: 0 };
  }
}