import assert from 'node:assert';
import path from 'path';
import { normalizePath } from './path.js';
import { McpError, ErrorCode } from "@modelcontextprotocol/sdk/types.js";

describe('normalizePath', () => {
  it('should normalize Windows paths', () => {
    const result = normalizePath('C:\\Users\\test\\path');
    assert.strictEqual(result, 'C:/Users/test/path');
  });

  it('should handle Unix paths', () => {
    const result = normalizePath('/Users/test/path');
    assert.strictEqual(result, '/Users/test/path');
  });

  it('should throw on invalid paths', () => {
    assert.throws(() => {
      normalizePath('');
    }, McpError);
  });
});
