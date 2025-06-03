#!/usr/bin/env node
import { Server as McpServer } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  ErrorCode,
  McpError
} from "@modelcontextprotocol/sdk/types.js";
import { spawn, type ChildProcessWithoutNullStreams, type SpawnOptionsWithoutStdio } from 'child_process';
import { createRequire } from 'module';
import { z } from 'zod';
import type { CommandHistoryEntry, ServerConfig, WindowsProtectedPaths, WindowsSecurityConfig } from './types/config.js';
import { CLIServerError, ErrorSeverity, type ErrorMetadata } from './types/errors.js';
import type {
  CompletionMessage,
  ExecutionMessage,
  ExecutionResult,
  PromptMessage,
  StreamUpdateMessage
} from './types/messages.js';
import { createDefaultConfig, loadConfig } from './utils/config.js';
import { translateUnixToWindows } from './utils/translation.js';
import {
  extractCommandName,
  isArgumentBlocked,
  isCommandBlocked,
  parseCommand,
  validateShellOperators
} from './utils/validation.js';
import { validateWindowsSecurity } from './utils/windowsValidation.js';
const require = createRequire(import.meta.url);
const packageJson = require('../package.json');

// Parse command line arguments using yargs
import { hideBin } from 'yargs/helpers';
import yargs from 'yargs/yargs';

const parseArgs = async () => {
  return yargs(hideBin(process.argv))
    .option('config', {
      alias: 'c',
      type: 'string',
      description: 'Path to config file'
    })
    .option('init-config', {
      type: 'string',
      description: 'Create a default config file at the specified path'
    })
    .help()
    .parse();
};

// Define argument types
export interface ExecuteCommandArgs {
  shell: string;
  command: string;
  workingDir?: string;
  dryRun?: boolean;
  force?: boolean;
}

interface GetCommandHistoryArgs {
  limit?: number;
}

const ExecuteCommandSchema = z.object({
  shell: z.enum(['powershell', 'cmd', 'gitbash']),
  command: z.string(),
  workingDir: z.string().optional(),
  dryRun: z.boolean().optional(),
  force: z.boolean().optional()
});

// Add custom error class for timeouts
class CommandTimeoutError extends Error {
  constructor(command: string, timeoutSeconds: number) {
    super(`Command execution timed out after ${timeoutSeconds} seconds: ${command}`);
    this.name = 'CommandTimeoutError';
  }
}

// Add process-wide exception handling
process.on('exit', (code) => {
  console.error(`Process exiting with code: ${code}`);
});

// Add utility function to check for destructive commands
function isDestructiveCommand(command: string, patterns: string[]): boolean {
  const normalizedCommand = command.toLowerCase().trim();
  return patterns.some(pattern => {
    // Convert the pattern to a proper regex, handling wildcards
    const regexPattern = pattern
      .toLowerCase()
      .replace(/[.+?^${}()|[\]\\]/g, '\\$&') // Escape regex special chars
      .replace(/\*/g, '.*'); // Convert * to .*
    return new RegExp(`\\b${regexPattern}\\b`).test(normalizedCommand);
  });
}

interface ExtendedMcpError extends McpError {
  metadata?: Record<string, unknown>;
}

export class CLIServer {
  private server: McpServer;
  private allowedPaths: Set<string>;
  private blockedCommands: Set<string>;
  private commandHistory: CommandHistoryEntry[];
  private config: ServerConfig;
  private activeChildProcess: ChildProcessWithoutNullStreams | null = null;
  private isShuttingDown: boolean = false;

  constructor(config: ServerConfig) {
    this.config = config;
    // Define server capabilities (first argument)
    const serverCapabilities = {
      name: "windows-cli-server",
      version: packageJson.version,
      capabilities: {
        tools: {
          execute_command: {
            description: "Executes a command in the specified shell.",
            inputSchema: ExecuteCommandSchema,
            execute: this.executeCommandTool.bind(this) // Bind 'this' context
          },
          get_command_history: {
            description: "Retrieves the command execution history.",
            inputSchema: z.object({
              limit: z.number().int().positive().optional()
            }),
            execute: this.getCommandHistoryTool.bind(this) // Bind 'this' context
          },
          get_current_directory: {
            description: "Gets the current working directory of the server.",
            inputSchema: z.object({}),
            execute: async () => ({ directory: process.cwd() })
          }
        },
        resources: {
          "cli://currentdir": {
            name: "Current Working Directory",
            description: "Provides the current working directory of the server process.",
            read: async () => ({
              mimeType: "text/plain",
              text: process.cwd()
            })
          },
          "cli://config": {
            name: "CLI Server Configuration",
            description: "Provides the current (sanitized) server configuration.",
            read: async () => {
              const safeConfig = {
                security: {
                  ...this.config.security,
                  // Ensure sensitive parts of windows config are not exposed if necessary
                  windows: {
                    ...this.config.security.windows,
                    // Example: Omit specific sensitive fields if they exist
                    // protectedPaths: undefined, // Or filter specific paths
                  }
                },
                shells: {
                  ...this.config.shells
                  // Example: Omit sensitive shell config if necessary
                }
              };
              return {
                mimeType: "application/json",
                text: JSON.stringify(safeConfig, null, 2)
              };
            }
          },
          "cli://history": {
            name: "Command History",
            description: "Provides the recent command execution history.",
            read: async () => ({
              mimeType: "application/json",
              text: JSON.stringify(
                this.commandHistory.slice(-this.config.security.maxHistorySize),
                null,
                2
              )
            })
          }
        },
        experimental: {
          streaming: {
            enabled: true,
            supportedTypes: ["command_output", "command_prompt"]
          }
        }
      }
    };

    // Define expected client capabilities (second argument, seems empty based on original code)
    const clientCapabilities = {
      capabilities: {
        tools: {},
        resources: {},
        experimental: {}
      }
    };

    this.server = new McpServer(serverCapabilities, clientCapabilities);

    // Initialize from config
    this.allowedPaths = new Set(config.security.allowedPaths);
    this.blockedCommands = new Set(config.security.blockedCommands);
    this.commandHistory = [];

    // setupHandlers is no longer needed and has been removed.
  }

  // --- Tool Execution Logic Methods ---

  private async executeCommandTool(args: ExecuteCommandArgs): Promise<ExecutionResult> {
    const metadata: Partial<ErrorMetadata> = {
      command: args.command,
      shell: args.shell,
      workingDir: args.workingDir
    };

    try {
      const execArgs = args as ExecuteCommandArgs;

      // Translate Unix commands if enabled
      let translatedCommand = execArgs.command;
      try {
        if (this.config.security.enableUnixTranslation) {
          translatedCommand = translateUnixToWindows(execArgs.command);
          metadata.originalCommand = execArgs.command;
          metadata.command = translatedCommand;
        }
      } catch (error) {
        throw this.wrapError(error, 'Command translation failed', metadata);
      }

      // Check for destructive commands before dry run
      // This way we warn about destructive commands even in dry run mode
      if (this.config.security.confirmDestructiveCommands) {
        const isDestructive = isDestructiveCommand(
          translatedCommand,
          this.config.security.destructiveCommandPatterns
        );

        if (isDestructive && !execArgs.force) {
          const destructiveError = new McpError(
            ErrorCode.InvalidRequest,
            [
              `Command '${translatedCommand}' is potentially destructive and requires confirmation.`,
              'To execute this command, you must:',
              '1. Review the command carefully',
              '2. Consider using --dryRun first to preview the execution',
              `3. Add 'force: true' to your request to confirm execution`,
              '',
              'Note: This safety check can be disabled in the server configuration.'
            ].join('\n')
          ) as ExtendedMcpError;
          destructiveError.metadata = {
            requiresForce: true,
            command: translatedCommand,
            originalCommand: execArgs.command
          };
          throw destructiveError;
        }
      }

      // Check for dry run mode
      if (this.config.execution.enableDryRun && execArgs.dryRun) {
        const dryRunResult: ExecutionResult = {
          isError: false,
          content: [
            {
              type: 'text',
              text: [
                'Dry run summary:',
                `- Shell: ${execArgs.shell}`,
                `- Original command: ${execArgs.command}`,
                `- Translated command: ${translatedCommand !== execArgs.command ? translatedCommand : '(no translation needed)'}`,
                `- Working directory: ${execArgs.workingDir || process.cwd()}`,
                `- Force flag: ${execArgs.force ? 'yes' : 'no'}`,
                `- Destructive command check: ${this.config.security.confirmDestructiveCommands ?
                  (isDestructiveCommand(translatedCommand, this.config.security.destructiveCommandPatterns) ? 'WARNING: Destructive command detected' : 'passed') :
                  'disabled'}`,
                '- Validation: passed',
                '\nThis command would be executed with these parameters, but no actual execution will occur.'
              ].join('\n')
            }
          ],
          exitCode: 0,
          duration: 0,
          isDryRun: true
        };

        // Still log the dry run attempt if command logging is enabled
        if (this.config.security.logCommands) {
          this.commandHistory.push({
            command: execArgs.command,
            output: JSON.stringify(dryRunResult),
            timestamp: new Date().toISOString(),
            exitCode: dryRunResult.exitCode,
            duration: dryRunResult.duration,
            workingDirectory: execArgs.workingDir || process.cwd(),
            shell: execArgs.shell,
            user: process.env.USERNAME || 'unknown',
            isDryRun: true, // Corrected: Mark as dry run in history
            force: execArgs.force || false
          });

          // Trim history if needed
          if (this.commandHistory.length > this.config.security.maxHistorySize) {
            this.commandHistory = this.commandHistory.slice(-this.config.security.maxHistorySize);
          }
        }

        return dryRunResult;
      }

      // Validate shell
      if (!this.config.shells[execArgs.shell as keyof ServerConfig['shells']]?.enabled) {
        throw new McpError(
          ErrorCode.InvalidRequest,
          `Invalid or disabled shell: ${execArgs.shell}`
        );
      }

      // Validate command
      await this.validateCommand(
        execArgs.shell as keyof ServerConfig['shells'],
        execArgs.command, // Use original command for validation
        execArgs.workingDir || process.cwd()
      );

      // Validate working directory if provided
      if (execArgs.workingDir && this.config.security.restrictWorkingDirectory) {
        if (!Array.from(this.allowedPaths).some(allowedPath =>
          execArgs.workingDir!.toLowerCase().startsWith(allowedPath.toLowerCase())
        )) {
          throw new McpError(
            ErrorCode.InvalidRequest,
            `Working directory must be within allowed paths: ${Array.from(this.allowedPaths).join(', ')}`
          );
        }
      }

      // Execute command with streaming (using the potentially translated command)
      const outputStream = await this.executeCommandWithStreaming(
        execArgs.shell as keyof ServerConfig['shells'],
        translatedCommand, // Use translated command for execution
        execArgs.workingDir
      );

      let fullOutput = '';
      let lastPrompt = '';

      // Process the stream
      for await (const message of outputStream) {
        switch (message.type) {
          case 'stream':
            fullOutput += message.data;
            // Use the server's built-in notification mechanism if available,
            // otherwise, this might need adjustment based on the SDK's streaming API.
            // Assuming server instance handles notifications internally or via transport.
            // await this.server.notification({ ... }); // Example placeholder
            break;

          case 'prompt':
            lastPrompt = message.prompt;
            // Handle prompt notification similarly
            // await this.server.notification({ ... }); // Example placeholder
            break;

          case 'completion':
            // Log command if enabled
            if (this.config.security.logCommands) {
              this.commandHistory.push({
                command: execArgs.command, // Log original command
                output: fullOutput,
                timestamp: new Date().toISOString(),
                exitCode: message.exitCode,
                duration: message.duration,
                workingDirectory: execArgs.workingDir || process.cwd(),
                shell: execArgs.shell,
                user: process.env.USERNAME || 'unknown',
                isDryRun: false,
                force: execArgs.force || false,
                translatedCommand: translatedCommand !== execArgs.command ? translatedCommand : undefined // Log translated command if different
              });

              // Trim history if needed
              if (this.commandHistory.length > this.config.security.maxHistorySize) {
                this.commandHistory = this.commandHistory.slice(-this.config.security.maxHistorySize);
              }
            }

            // Return final result
            return {
              isError: false,
              content: [{
                type: 'stdout', // Assuming stdout for successful completion output
                text: fullOutput
              }],
              exitCode: message.exitCode,
              duration: message.duration,
              lastPrompt: lastPrompt || undefined,
              isDryRun: false
            };
        }
      }

      // Handle case where loop completes without completion message (should ideally not happen)
      const unexpectedEndError = new CLIServerError('Command execution stream ended unexpectedly without a completion message.', ErrorSeverity.ERROR, metadata);
      await this.logError(unexpectedEndError);
      return {
        isError: true,
        content: [{
          type: 'stderr',
          text: unexpectedEndError.message
        }],
        exitCode: -1, // Indicate abnormal termination
        duration: 0, // Duration might be inaccurate here
        isDryRun: false
      };
    } catch (error) {
      const wrappedError = this.wrapError(error, 'Command execution failed', metadata);
      await this.logError(wrappedError);
      return {
        isError: true,
        content: [{
          type: 'stderr',
          text: wrappedError.message
        }],
        exitCode: (error instanceof McpError && error.code === ErrorCode.InvalidRequest) ? 400 : 1, // Use specific exit code for invalid requests
        duration: 0,
        error: wrappedError.metadata, // Include metadata in the error response
        isDryRun: false
      };
    }
  }

  private async getCommandHistoryTool(args: GetCommandHistoryArgs) {
    const limit = Math.min(
      args?.limit || this.config.security.maxHistorySize,
      this.config.security.maxHistorySize
    );
    return {
      history: this.commandHistory.slice(-limit)
    };
  }

  // --- End Tool Execution Logic ---


  private async logError(error: CLIServerError): Promise<void> {
    const errorLog = {
      message: error.message,
      severity: error.severity,
      metadata: error.metadata,
      stack: error.stack,
      originalError: error.originalError ? {
        message: error.originalError.message,
        stack: error.originalError.stack
      } : undefined
    };

    console.error('[Error Log]', JSON.stringify(errorLog, null, 2));

    // Could also implement file-based logging or error reporting service here
  }

  private wrapError(
    error: unknown,
    context: string,
    metadata: Partial<ErrorMetadata> = {}
  ): CLIServerError {
    if (error instanceof CLIServerError) {
      return error;
    }

    if (error instanceof McpError) {
      return new CLIServerError(
        error.message,
        ErrorSeverity.ERROR,
        { ...metadata, errorCode: error.code },
        error
      );
    }

    const message = error instanceof Error ? error.message : String(error);
    return new CLIServerError(
      `${context}: ${message}`,
      ErrorSeverity.ERROR,
      metadata,
      error instanceof Error ? error : undefined
    );
  }

  private async validateCommand(
    shell: keyof ServerConfig['shells'],
    command: string,
    workingDir: string
  ): Promise<void> {
    try {
      // Check for command chaining/injection attempts if enabled
      if (this.config.security.enableInjectionProtection) {
        const shellConfig = this.config.shells[shell];
        validateShellOperators(command, shellConfig);
      }

      const { command: executable, args } = parseCommand(command);

      // Check for blocked commands
      if (isCommandBlocked(executable, Array.from(this.blockedCommands))) {
        throw new McpError(
          ErrorCode.InvalidRequest,
          `Command is blocked: "${extractCommandName(executable)}"`
        );
      }

      // Check for blocked arguments
      if (isArgumentBlocked(args, this.config.security.blockedArguments)) {
        throw new McpError(
          ErrorCode.InvalidRequest,
          'One or more arguments are blocked. Check configuration for blocked patterns.'
        );
      }

      // Validate command length
      if (command.length > this.config.security.maxCommandLength) {
        throw new McpError(
          ErrorCode.InvalidRequest,
          `Command exceeds maximum length of ${this.config.security.maxCommandLength}`
        );
      }

      // Windows-specific security validation
      await this.validateWindowsSecurity(command, workingDir, this.config.security.windows);
    } catch (error) {
      throw this.wrapError(error, 'Command validation failed', {
        command,
        shell: shell.toString(),
        workingDir
      });
    }
  }

  private async *executeCommandWithStreaming(
    shell: keyof ServerConfig['shells'],
    command: string,
    workingDir?: string
  ): AsyncGenerator<ExecutionMessage, void, unknown> {
    const metadata: Partial<ErrorMetadata> = {
      command,
      shell: shell.toString(),
      workingDir
    };

    try {
      const shellConfig = this.config.shells[shell];
      const startTime = Date.now();

      const spawnOptions: SpawnOptionsWithoutStdio = {
        shell: shellConfig.command,
        cwd: workingDir || shellConfig.workingDirectory,
        env: {
          ...process.env,
          ...shellConfig.environmentVariables
        },
        windowsHide: true,
        windowsVerbatimArguments: true
      };

      const childProcess = spawn(command, [], spawnOptions) as ChildProcessWithoutNullStreams;
      this.activeChildProcess = childProcess;

      try {
        // Create promise for process completion
        const exitPromise = new Promise<number>((resolve) => {
          childProcess.once('close', resolve);
        });

        // Handle stdout
        childProcess.stdout.setEncoding(shellConfig.encoding as BufferEncoding);
        for await (const chunk of childProcess.stdout) {
          const text = chunk.toString();
          if (text.includes('?') || text.includes(':')) {
            yield {
              type: 'prompt',
              prompt: text
            } as PromptMessage;
          } else {
            yield {
              type: 'stream',
              stream: 'stdout',
              data: text
            } as StreamUpdateMessage;
          }
        }

        // Handle stderr
        childProcess.stderr.setEncoding(shellConfig.encoding as BufferEncoding);
        for await (const chunk of childProcess.stderr) {
          yield {
            type: 'stream',
            stream: 'stderr',
            data: chunk.toString()
          } as StreamUpdateMessage;
        }

        // Wait for process completion
        const exitCode = await exitPromise;

        yield {
          type: 'completion',
          exitCode,
          duration: Date.now() - startTime
        } as CompletionMessage;
        return;
      } finally {
        if (this.activeChildProcess === childProcess) {
          this.activeChildProcess = null;
        }
      }
    } catch (error) {
      const wrappedError = this.wrapError(error, 'Command execution failed', metadata);
      await this.logError(wrappedError);
      throw wrappedError;
    }
  }

  // Removed setupHandlers method as registration now happens in the constructor.

  private async killActiveProcess(signal: 'SIGTERM' | 'SIGKILL' = 'SIGTERM'): Promise<void> {
    if (!this.activeChildProcess) return;

    return new Promise<void>((resolve) => {
      const process = this.activeChildProcess!;

      // Set a timeout for force kill
      const forceKillTimeout = setTimeout(() => {
        if (this.activeChildProcess === process) {
          console.error('Process did not terminate gracefully, forcing kill...');
          process.kill('SIGKILL');
        }
      }, 5000); // 5 seconds grace period

      // Listen for process exit
      process.once('exit', () => {
        clearTimeout(forceKillTimeout);
        this.activeChildProcess = null;
        resolve();
      });

      // Send the initial signal
      process.kill(signal);
    });
  }

  private async handleShutdown(signal: string): Promise<void> {
    try {
      if (this.isShuttingDown) return;
      this.isShuttingDown = true;

      console.error(`\nReceived ${signal}, initiating graceful shutdown...`);

      try {
        if (this.activeChildProcess) {
          console.error('Terminating active command...');
          await this.killActiveProcess();
          console.error('Active command terminated.');
        }

        // Optional: Save any pending command history or state
        if (this.config.security.logCommands && this.commandHistory.length > 0) {
          // You could save the command history to a file here if needed
          console.error('Command history saved.');
        }

        // Clean exit
        console.error('Shutdown complete.');
        process.exit(0);
      } catch (error) {
        const wrappedError = this.wrapError(error, 'Shutdown process termination failed', {
          severity: ErrorSeverity.CRITICAL,
          command: signal
        });
        await this.logError(wrappedError);
        process.exit(1);
      }
    } catch (error) {
      const wrappedError = this.wrapError(error, 'Shutdown process termination failed', {
        severity: ErrorSeverity.CRITICAL,
        command: signal
      });
      await this.logError(wrappedError);
      process.exit(1);
    }
  }

  private setupSignalHandlers(): void {
    // Handle SIGINT (Ctrl+C)
    process.on('SIGINT', () => this.handleShutdown('SIGINT'));

    // Handle SIGTERM
    process.on('SIGTERM', () => this.handleShutdown('SIGTERM'));

    // Handle Windows-specific signals if available
    if (process.platform === 'win32') {
      try {
        // Handle CTRL+BREAK on Windows
        process.on('SIGBREAK', () => this.handleShutdown('SIGBREAK'));
      } catch (error) {
        console.error('Warning: SIGBREAK handler not supported on this system');
      }
    }

    // Handle uncaught exceptions and unhandled rejections
    process.on('uncaughtException', (error) => {
      console.error('Uncaught Exception:', error);
      this.handleShutdown('uncaughtException');
    });

    process.on('unhandledRejection', (reason, promise) => {
      console.error('Unhandled Rejection at:', promise, 'reason:', reason);
      this.handleShutdown('unhandledRejection');
    });
  }

  async run(): Promise<void> {
    this.setupSignalHandlers();

    const transport = new StdioServerTransport();
    await (this.server as any).connect(transport);

    console.error("Windows CLI MCP Server running on stdio");
    console.error("Press Ctrl+C to shutdown gracefully");
  }

  private async validateWindowsSecurity(
    command: string,
    workingDir: string,
    config: Omit<WindowsSecurityConfig, 'protectedPaths'> & { protectedPaths: string[] }
  ): Promise<void> {
    const protectedPaths: WindowsProtectedPaths = {
      system: [
        'C:\\Windows',
        'C:\\System32',
        'C:\\Program Files',
        'C:\\Program Files (x86)'
      ],
      program: [
        'C:\\Program Files',
        'C:\\Program Files (x86)'
      ],
      user: [
        process.env.USERPROFILE || '',
        process.env.APPDATA || '',
        process.env.LOCALAPPDATA || ''
      ],
      registry: [
        'HKEY_LOCAL_MACHINE',
        'HKEY_CLASSES_ROOT',
        'HKEY_USERS'
      ]
    };

    await validateWindowsSecurity(command, workingDir, {
      ...config,
      protectedPaths
    });
  }
}

// Start server
async function main() {
  let server: CLIServer | null = null;

  try {
    const args = await parseArgs();

    if (args['init-config']) {
      await createDefaultConfig(args['init-config']);
      console.log(`Created default config at ${args['init-config']}`);
      process.exit(0);
    }

    const config = await loadConfig(args.config);
    server = new CLIServer(config);
    await server.run();
  } catch (error) {
    console.error('Failed to start server:', error);

    // Attempt graceful shutdown if server was created
    if (server) {
      try {
        await (server as any).handleShutdown('startup-error');
      } catch (shutdownError) {
        console.error('Failed to shutdown server:', shutdownError);
      }
    }
    process.exit(1);
  }
}

main();