import { ServerConfig } from '../types/config.js';
import { promises as fs } from 'fs';
import path from 'path';
import { DEFAULT_PROTECTED_PATHS } from './windowsValidation.js';
import os from 'os';

// Ensure DEFAULT_PROTECTED_PATHS is typed as string[]
const protectedPaths: string[] = Array.isArray(DEFAULT_PROTECTED_PATHS)
  ? DEFAULT_PROTECTED_PATHS
  : Object.values(DEFAULT_PROTECTED_PATHS);

export async function loadConfig(configPath?: string): Promise<ServerConfig> {
  const defaultConfig: ServerConfig = {
    security: {
      maxCommandLength: 4096,
      blockedCommands: [
        'rm', 'del', 'format', 'reg', 'regedit',
        'taskkill', 'net', 'netsh', 'sc', 'wmic'
      ],
      blockedArguments: [
        '--system', '--admin', '--elevated',
        '/system', '/admin', '/elevated'
      ],
      allowedPaths: [
        process.cwd(),
        process.env.USERPROFILE || '',
        process.env.TEMP || '',
        'C:\\Users\\Public'
      ],
      restrictWorkingDirectory: true,
      logCommands: true,
      maxHistorySize: 1000,
      commandTimeout: 30000,
      enableInjectionProtection: true,
      enableUnixTranslation: false,
      confirmDestructiveCommands: true,
      destructiveCommandPatterns: [
        "del", "rm", "format", "Remove-Item", "rd", "rmdir",
        "deltree", "erase", "fdisk", "clean",
        "drop", "truncate", "shutdown", "taskkill /F",
        "reg delete", "wmic.*delete", "net user.*\\/delete"
      ],
      windows: {
        protectedPaths,
        allowSystemCommands: false,
        allowRegistryAccess: false,
        allowPowerShellScripts: true,
        allowBatchScripts: true,
        requireAdminWarning: true,
        useJobObjects: true,
        isolateProcesses: true,
        networkRestrictions: {
          allowOutbound: true,
          allowedHosts: ['localhost', '127.0.0.1'],
          blockedPorts: [3389, 445, 135, 137, 138, 139]
        },
        resourceLimits: {
          maxMemoryMB: 1024,
          maxCPUPercent: 50,
          maxProcesses: 10,
          maxFileSize: 100 * 1024 * 1024
        }
      },
      timeouts: {
        default: 30000,
        network: 60000,
        fileSystem: 45000,
        database: 90000
      },
      retry: {
        maxAttempts: 3,
        delayMs: 1000,
        exponentialBackoff: true
      },
      suggestCorrections: true,
      auditLog: {
        enabled: true,
        path: path.join(os.homedir(), '.win-cli-mcp', 'audit.log'),
        maxSize: 10 * 1024 * 1024,
        rotate: true
      }
    },
    execution: {
      enableDryRun: true,
      timeoutSeconds: 300,
      timeoutBehavior: 'kill'
    },
    shells: {
      powershell: {
        enabled: true,
        command: 'powershell.exe',
        args: ['-NoProfile', '-NonInteractive', '-Command'],
        blockedOperators: ['|', '>', '>>', '&', '&&', '||', ';'],
        environmentVariables: {
          'POWERSHELL_TELEMETRY_OPTOUT': '1',
          'NO_COLOR': '1'
        },
        workingDirectory: process.cwd(),
        encoding: 'utf8',
        timeout: 30000
      },
      cmd: {
        enabled: true,
        command: 'cmd.exe',
        args: ['/C'],
        blockedOperators: ['|', '>', '>>', '&', '&&', '||', ';'],
        environmentVariables: {
          'PROMPT': '$P$G',
          'NO_COLOR': '1'
        },
        workingDirectory: process.cwd(),
        encoding: 'utf8',
        timeout: 30000
      },
      gitbash: {
        enabled: true,
        command: 'C:\\Program Files\\Git\\bin\\bash.exe',
        args: ['-c'],
        blockedOperators: ['|', '>', '>>', '&', '&&', '||', ';'],
        environmentVariables: {
          'TERM': 'dumb',
          'NO_COLOR': '1'
        },
        workingDirectory: process.cwd(),
        encoding: 'utf8',
        timeout: 30000
      }
    }
  };

  if (!configPath) {
    return defaultConfig;
  }

  try {
    const configContent = await fs.readFile(configPath, 'utf8');
    const userConfig = JSON.parse(configContent);
    return { ...defaultConfig, ...userConfig };
  } catch (error) {
    console.error(`Failed to load config from ${configPath}:`, error);
    return defaultConfig;
  }
}

export async function createDefaultConfig(configPath: string): Promise<void> {
  const defaultConfig = await loadConfig();
  const configDir = path.dirname(configPath);

  try {
    await fs.mkdir(configDir, { recursive: true });
    await fs.writeFile(configPath, JSON.stringify(defaultConfig, null, 2));
  } catch (error) {
    throw new Error(`Failed to create default config at ${configPath}: ${error}`);
  }
}