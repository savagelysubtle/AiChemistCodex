import path from 'path';
import { exec } from 'child_process';
import { promisify } from 'util';
import type { ShellConfig } from '../types/config.js';
const execAsync = promisify(exec);

// Cache for resolved command paths
const commandPathCache = new Map<string, string | null>();

// Cache for compiled regexes
const blockedArgRegexCache = new Map<string, RegExp>();
const shellOperatorRegexCache = new Map<string, RegExp>();

// Cache for blocked command sets
const blockedCommandSetCache = new Map<string, Set<string>>();


export async function resolveCommandPath(command: string): Promise<string | null> {
    const lowerCaseCommand = command.toLowerCase();
    if (commandPathCache.has(lowerCaseCommand)) {
        return commandPathCache.get(lowerCaseCommand)!;
    }

    try {
        // Use the original command casing for 'where' as it might matter in some edge cases
        const { stdout } = await execAsync(`where "${command}"`, { encoding: 'utf8' });
        const resolvedPath = stdout.split('\n')[0].trim();
        commandPathCache.set(lowerCaseCommand, resolvedPath);
        return resolvedPath;
    } catch {
        commandPathCache.set(lowerCaseCommand, null); // Cache the failure too
        return null;
    }
}

export function extractCommandName(command: string): string {
    // Remove any path components
    const basename = path.basename(command);
    // Remove extension
    return basename.replace(/\.(exe|cmd|bat)$/i, '').toLowerCase();
}

export function isCommandBlocked(command: string, blockedCommands: string[]): boolean {
    const commandName = extractCommandName(command.toLowerCase());

    // Use a Set for efficient lookup
    const blockedCommandsKey = JSON.stringify(blockedCommands.sort()); // Key for caching the Set
    let blockedSet = blockedCommandSetCache.get(blockedCommandsKey);

    if (!blockedSet) {
        blockedSet = new Set<string>();
        blockedCommands.forEach(blocked => {
            const lowerBlocked = blocked.toLowerCase();
            blockedSet!.add(lowerBlocked);
            // Add variations with common extensions
            blockedSet!.add(`${lowerBlocked}.exe`);
            blockedSet!.add(`${lowerBlocked}.cmd`);
            blockedSet!.add(`${lowerBlocked}.bat`);
        });
        blockedCommandSetCache.set(blockedCommandsKey, blockedSet);
    }


    // Check against the Set (includes variations with extensions)
    return blockedSet.has(commandName);
}

export function isArgumentBlocked(args: string[], blockedArguments: string[]): boolean {
    // Pre-compile or retrieve regexes from cache
    const regexes = blockedArguments.map(blocked => {
        const cacheKey = `^${blocked}$_i`; // Include flags in key
        if (!blockedArgRegexCache.has(cacheKey)) {
            blockedArgRegexCache.set(cacheKey, new RegExp(`^${blocked}$`, 'i'));
        }
        return blockedArgRegexCache.get(cacheKey)!;
    });

    return args.some(arg =>
        regexes.some(regex => regex.test(arg))
    );
}

/**
 * Validates a command for a specific shell, checking for shell-specific blocked operators
 */
export function validateShellOperators(command: string, shellConfig: ShellConfig): void {
    // Skip validation if shell doesn't specify blocked operators
    if (!shellConfig.blockedOperators?.length) {
        return;
    }

    // Create or retrieve regex pattern from cache
    const cacheKey = JSON.stringify(shellConfig.blockedOperators.sort()); // Key based on sorted operators
    let regex = shellOperatorRegexCache.get(cacheKey);

    if (!regex) {
        const operatorPattern = shellConfig.blockedOperators
            .map(op => op.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')) // Escape regex special chars
            .join('|');
        regex = new RegExp(operatorPattern);
        shellOperatorRegexCache.set(cacheKey, regex);
    }

    if (regex.test(command)) {
        throw new Error(`Command contains blocked operators for this shell: ${shellConfig.blockedOperators.join(', ')}`);
    }
}

/**
 * Parse a command string into command and arguments, properly handling paths with spaces and quotes
 */
export function parseCommand(fullCommand: string): { command: string; args: string[] } {
    fullCommand = fullCommand.trim();
    if (!fullCommand) {
        return { command: '', args: [] };
    }

    const tokens: string[] = [];
    let current = '';
    let inQuotes = false;
    let quoteChar = '';

    // Parse into tokens, preserving quoted strings
    for (let i = 0; i < fullCommand.length; i++) {
        const char = fullCommand[i];

        // Handle quotes
        if ((char === '"' || char === "'") && (!inQuotes || char === quoteChar)) {
            if (inQuotes) {
                tokens.push(current);
                current = '';
            }
            inQuotes = !inQuotes;
            quoteChar = inQuotes ? char : '';
            continue;
        }

        // Handle spaces outside quotes
        if (char === ' ' && !inQuotes) {
            if (current) {
                tokens.push(current);
                current = '';
            }
            continue;
        }

        current += char;
    }

    // Add any remaining token
    if (current) {
        tokens.push(current);
    }

    // Handle empty input
    if (tokens.length === 0) {
        return { command: '', args: [] };
    }

    // First, check if this is a single-token command
    if (!tokens[0].includes(' ') && !tokens[0].includes('\\')) {
        return {
            command: tokens[0],
            args: tokens.slice(1)
        };
    }

    // Special handling for Windows paths with spaces
    let commandTokens: string[] = [];
    let i = 0;

    // Keep processing tokens until we find a complete command path
    while (i < tokens.length) {
        commandTokens.push(tokens[i]);
        const potentialCommand = commandTokens.join(' ');

        // Check if this could be a complete command path
        if (/\.(exe|cmd|bat)$/i.test(potentialCommand) ||
            (!potentialCommand.includes('\\') && commandTokens.length === 1)) {
            return {
                command: potentialCommand,
                args: tokens.slice(i + 1)
            };
        }

        // If this is part of a path, keep looking
        if (potentialCommand.includes('\\')) {
            i++;
            continue;
        }

        // If we get here, treat the first token as the command
        return {
            command: tokens[0],
            args: tokens.slice(1)
        };
    }

    // If we get here, use all collected tokens as the command
    return {
        command: commandTokens.join(' '),
        args: tokens.slice(commandTokens.length)
    };
}

export function isPathAllowed(testPath: string, allowedPaths: string[]): boolean {
    const normalizedPath = path.normalize(testPath).toLowerCase();
    return allowedPaths.some(allowedPath => {
        const normalizedAllowedPath = path.normalize(allowedPath).toLowerCase();
        return normalizedPath.startsWith(normalizedAllowedPath);
    });
}

export function validateWorkingDirectory(dir: string, allowedPaths: string[]): void {
    if (!path.isAbsolute(dir)) {
        throw new Error('Working directory must be an absolute path');
    }

    if (!isPathAllowed(dir, allowedPaths)) {
        const allowedPathsStr = allowedPaths.join(', ');
        throw new Error(
            `Working directory must be within allowed paths: ${allowedPathsStr}`
        );
    }
}

export function normalizeWindowsPath(inputPath: string): string {
    // Convert forward slashes to backslashes
    let normalized = inputPath.replace(/\//g, '\\');

    // Handle Windows drive letter
    if (/^[a-zA-Z]:\\.+/.test(normalized)) {
        // Already in correct form
        return path.normalize(normalized);
    }

    // Handle paths without drive letter
    if (normalized.startsWith('\\')) {
        // Assume C: drive if not specified
        normalized = `C:${normalized}`;
    }

    return path.normalize(normalized);
}