type CommandMapping = {
  [key: string]: string | ((args: string[]) => string);
};

const UNIX_TO_WINDOWS_COMMANDS: CommandMapping = {
  'ls': 'dir',
  'pwd': 'cd',
  'cp': 'copy',
  'mv': 'move',
  'rm': 'del',
  'mkdir': 'md',
  'rmdir': 'rd',
  'cat': 'type',
  'clear': 'cls',
  'touch': (args: string[]) => `echo. > ${args[0]}`,
  'ln': (args: string[]) => `mklink ${args.join(' ')}`,
  'grep': 'findstr',
  'kill': 'taskkill',
  'ps': 'tasklist',
  'chmod': 'icacls',
  'chown': 'icacls'
};

const COMMON_FLAGS_TRANSLATION: { [key: string]: string } = {
  '-r': '/s',
  '-R': '/s',
  '-f': '/f',
  '-p': '/p',
  '-v': '/v'
};

export function translateUnixToWindows(command: string): string {
  try {
    // Split command and arguments while preserving quoted strings
    const parts = command.match(/(?:[^\s"']+|"[^"]*"|'[^']*')+/g);
    if (!parts || parts.length === 0) return command;

    const baseCommand = parts[0].toLowerCase();
    const args = parts.slice(1);

    // Check if command exists in mapping
    const windowsCommand = UNIX_TO_WINDOWS_COMMANDS[baseCommand];
    if (!windowsCommand) return command; // Return original if no mapping exists

    // Handle function-based translations
    if (typeof windowsCommand === 'function') {
      try {
        return windowsCommand(args);
      } catch (error) {
        console.error(`Translation function failed for command ${baseCommand}:`, error);
        return command; // Return original on translation function failure
      }
    }

    // Translate flags if present
    const translatedArgs = args.map(arg => {
      if (arg.startsWith('-')) {
        return COMMON_FLAGS_TRANSLATION[arg] || arg;
      }
      return arg;
    });

    return `${windowsCommand} ${translatedArgs.join(' ')}`.trim();
  } catch (error) {
    console.error('Command translation failed:', error);
    return command; // Return original command on error
  }
}

// Helper function to check if a command needs translation
export function isUnixCommand(command: string): boolean {
  const baseCommand = command.split(' ')[0].toLowerCase();
  return baseCommand in UNIX_TO_WINDOWS_COMMANDS;
}