import { z } from "zod";
import { Tool } from "../types.js";
import { McpError, ErrorCode } from "@modelcontextprotocol/sdk/types.js";
import { createSchemaHandler } from "./schema.js";
import { VaultResolver } from "./vault-resolver.js";

export interface BaseToolConfig<T> {
  name: string;
  description: string;
  schema?: z.ZodType<any>;
  handler: (
    args: T,
    sourcePath: string,
    sourceVaultName: string,
    destinationPath?: string,
    destinationVaultName?: string,
    isCrossVault?: boolean
  ) => Promise<any>;
}

/**
 * Creates a standardized tool with common error handling and vault validation
 */
export function createTool<T extends { vault: string }>(
  config: BaseToolConfig<T>,
  vaults: Map<string, string>
): Tool {
  const vaultResolver = new VaultResolver(vaults);
  const schemaHandler = config.schema ? createSchemaHandler(config.schema) : undefined;

  return {
    name: config.name,
    description: config.description,
    inputSchema: schemaHandler || createSchemaHandler(z.object({})),
    handler: async (args) => {
      try {
        const validated = schemaHandler ? schemaHandler.parse(args) as T : {} as T;
        const { vaultPath, vaultName } = vaultResolver.resolveVault(validated.vault);
        return await config.handler(validated, vaultPath, vaultName);
      } catch (error) {
        if (error instanceof z.ZodError) {
          throw new McpError(
            ErrorCode.InvalidRequest,
            `Invalid arguments: ${error.errors.map(e => e.message).join(", ")}`
          );
        }
        throw error;
      }
    }
  };
}

/**
 * Creates a tool that requires no arguments
 */
export function createToolNoArgs(
  config: Omit<BaseToolConfig<{}>, "schema">,
  vaults: Map<string, string>
): Tool {
  const vaultResolver = new VaultResolver(vaults);

  // Get first vault for default if available
  const firstVault = vaults.entries().next().value;
  const defaultVaultName = firstVault ? firstVault[0] : "";
  const defaultVaultPath = firstVault ? firstVault[1] : "";

  return {
    name: config.name,
    description: config.description,
    inputSchema: createSchemaHandler(z.object({})),
    handler: async () => {
      try {
        console.error(`[Debug] ${config.name}: Tool handler started`);
        console.error(`[Debug] ${config.name}: Default vault: ${defaultVaultName} at ${defaultVaultPath}`);
        console.error(`[Debug] ${config.name}: Total vaults available: ${vaults.size}`);

        // Pass the default vault information to the handler
        return await config.handler({}, defaultVaultPath, defaultVaultName);
      } catch (error) {
        console.error(`[Error] ${config.name}: Handler failed: ${error instanceof Error ? error.message : String(error)}`);
        if (error instanceof Error && error.stack) {
          console.error(`[Error] ${config.name}: Stack trace: ${error.stack}`);
        }
        throw error;
      }
    }
  };
}

/**
 * Creates a standardized tool that operates between two vaults
 */

// NOT IN USE

/*
export function createDualVaultTool<T extends { sourceVault: string; destinationVault: string }>(
  config: BaseToolConfig<T>,
  vaults: Map<string, string>
): Tool {
  const vaultResolver = new VaultResolver(vaults);
  const schemaHandler = createSchemaHandler(config.schema);

  return {
    name: config.name,
    description: config.description,
    inputSchema: schemaHandler,
    handler: async (args) => {
      try {
        const validated = schemaHandler.parse(args) as T;
        const { source, destination, isCrossVault } = vaultResolver.resolveDualVaults(
          validated.sourceVault,
          validated.destinationVault
        );
        return await config.handler(
          validated,
          source.vaultPath,
          source.vaultName,
          destination.vaultPath,
          destination.vaultName,
          isCrossVault
        );
      } catch (error) {
        if (error instanceof z.ZodError) {
          throw new McpError(
            ErrorCode.InvalidRequest,
            `Invalid arguments: ${error.errors.map(e => e.message).join(", ")}`
          );
        }
        throw error;
      }
    }
  };
}
*/
