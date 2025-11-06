/**
 * MCP Client Stub
 *
 * This module provides function stubs that route to the real MCP implementation when
 * running inside the harness.
 *
 * IMPORTANT: This code follows the pattern from "Code Execution with MCP" where:
 *
 * 1. The agent writes code that imports and calls these TypeScript functions
 * 2. At runtime, the stub checks if MCP_HARNESS_ACTIVE environment variable is set
 * 3. If active, dynamically imports and delegates to the real MCP implementation
 * 4. The real implementation handles MCP protocol communication with servers
 *
 * The agent never implements MCP protocol itself - that's the harness's job.
 *
 * How routing works:
 * - When harness runs: MCP_HARNESS_ACTIVE=true → routes to runtime/mcp-client-impl.ts
 * - When run directly: throws helpful error telling you to use the harness
 */

export interface McpToolResult {
  content: any;
  isError?: boolean;
}

/**
 * Call an MCP tool using the identifier pattern from the article
 *
 * This stub function routes to the real MCP implementation when running in the harness.
 *
 * Flow:
 * 1. Agent writes: callMcpTool('github__search_code', {...})
 * 2. This function checks MCP_HARNESS_ACTIVE environment variable
 * 3. If active: dynamically imports runtime/mcp-client-impl.ts
 * 4. Real implementation connects to MCP server and makes the call
 * 5. Result flows back to agent's code
 *
 * @param toolIdentifier - Combined identifier in format "serverName__toolName"
 * @param input - Parameters to pass to the tool
 * @returns The result from the MCP tool
 *
 * @example
 * // Agent writes this code:
 * const result = await callMcpTool('github__search_code', {
 *   query: 'language:TypeScript'
 * });
 *
 * // At runtime, this function:
 * // 1. Checks process.env.MCP_HARNESS_ACTIVE
 * // 2. Imports real implementation from runtime/mcp-client-impl.ts
 * // 3. Delegates to real implementation which:
 * //    - Parses identifier to get server="github", tool="search_code"
 * //    - Connects to github MCP server (lazily, on first call)
 * //    - Sends tools/call request via MCP protocol
 * //    - Returns result
 */
export async function callMcpTool<T = any>(
  toolIdentifier: string,
  input: Record<string, any>
): Promise<T> {
  // Check if running inside harness (environment variable set by harness)
  if (process.env.MCP_HARNESS_ACTIVE === 'true') {
    // Route to real implementation via dynamic import
    const { callMcpTool: realCallMcpTool } = await import('../runtime/mcp-client-impl.js');
    return realCallMcpTool(toolIdentifier, input);
  }

  // Not running in harness - provide helpful error message
  throw new Error(
    `callMcpTool requires the MCP harness to be active.\n\n` +
    `Attempted: ${toolIdentifier}\n` +
    `Input: ${JSON.stringify(input, null, 2)}\n\n` +
    `The harness:\n` +
    `1. Sets MCP_HARNESS_ACTIVE=true environment variable\n` +
    `2. This stub detects it and routes to the real implementation\n` +
    `3. Real implementation handles MCP protocol communication\n\n` +
    `Run your script with: npm run exec workspace/your-script.ts\n` +
    `See: docs/code-execution-with-mcp.md for details.`
  );
}
