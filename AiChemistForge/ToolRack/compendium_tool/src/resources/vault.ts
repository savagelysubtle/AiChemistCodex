import { z } from 'zod';

export const VaultSchema = z.object({
  name: z.string(),
  path: z.string(),
});

export type Vault = z.infer<typeof VaultSchema>;

export interface VaultOperationResult {
  success: boolean;
  message: string;
  vault?: Vault;
}