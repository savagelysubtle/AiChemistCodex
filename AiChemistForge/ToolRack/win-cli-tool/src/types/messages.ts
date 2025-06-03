export interface StreamUpdateMessage {
  type: 'stream';
  stream: 'stdout' | 'stderr';
  data: string;
}

export interface PromptMessage {
  type: 'prompt';
  prompt: string;
}

export interface CompletionMessage {
  type: 'completion';
  exitCode: number;
  duration: number;
}

export type ExecutionMessage = StreamUpdateMessage | PromptMessage | CompletionMessage;

export interface ExecutionResult {
  isError: boolean;
  content: Array<{
    type: 'stdout' | 'stderr' | 'text';
    text: string;
  }>;
  exitCode: number;
  duration: number;
  lastPrompt?: string;
  isDryRun?: boolean;
  error?: Record<string, unknown>;
}