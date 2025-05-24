import { createToolResponse } from "../../utils/responses.js";
import { createToolNoArgs } from "../../utils/tool-factory.js";

export const createListAvailableVaultsTool = (vaults: Map<string, string>) => {
  return createToolNoArgs({
    name: "list_available_vaults",
    description: "Lists all available vaults that can be used with other tools",
    handler: async () => {
      try {
        console.error(`[Debug] list_available_vaults: Starting tool execution`);
        console.error(`[Debug] list_available_vaults: Number of vaults: ${vaults.size}`);

        const availableVaults = Array.from(vaults.keys());
        console.error(`[Debug] list_available_vaults: Retrieved ${availableVaults.length} vault names`);

        if (availableVaults.length === 0) {
          console.error(`[Debug] list_available_vaults: No vaults available`);
          return createToolResponse("No vaults are currently available");
        }

        const message = [
          "Available vaults:",
          ...availableVaults.map(vault => `  - ${vault}`)
        ].join('\n');

        console.error(`[Debug] list_available_vaults: Successfully created response message`);
        return createToolResponse(message);
      } catch (error) {
        console.error(`[Error] list_available_vaults failed: ${error instanceof Error ? error.message : String(error)}`);
        if (error instanceof Error && error.stack) {
          console.error(`[Error] Stack trace: ${error.stack}`);
        }
        // Rethrow as a formatted response to prevent hanging
        return createToolResponse(`Error listing vaults: ${error instanceof Error ? error.message : String(error)}`);
      }
    }
  }, vaults);
}
