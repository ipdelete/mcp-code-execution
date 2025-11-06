/**
 * MCP Client
 * 
 * This module provides function stubs that are intercepted by the agent harness.
 * 
 * IMPORTANT: This code follows the pattern from "Code Execution with MCP" where:
 * 
 * 1. The agent writes code that imports and calls these TypeScript functions
 * 2. The agent harness intercepts these calls at runtime
 * 3. The harness translates them into actual MCP protocol requests
 * 4. Results are returned as if the function executed normally
 * 
 * The agent never implements MCP protocol itself - that's the harness's job.
 * 
 * From the article (lines 77-123):
 * > "When the model writes code that imports and calls these functions, the agent 
 * > harness intercepts the calls and translates them into MCP tool requests behind 
 * > the scenes."
 */

export interface McpToolResult {
  content: any;
  isError?: boolean;
}

/**
 * Call an MCP tool on a specific server
 * 
 * This function is intended to be INTERCEPTED by the agent harness.
 * The harness will:
 * 1. Catch this function call
 * 2. Execute the actual MCP protocol communication
 * 3. Return the result as if this function executed normally
 * 
 * @param serverName - Name of the MCP server (e.g., 'github-mcp-server')
 * @param toolName - Name of the tool to call (e.g., 'search_code')
 * @param params - Parameters to pass to the tool
 * @returns The result from the MCP tool
 * 
 * @example
 * // Agent writes this code:
 * const result = await callMcpTool('github-mcp-server', 'search_code', {
 *   query: 'language:TypeScript'
 * });
 * 
 * // Harness intercepts and executes:
 * // 1. Connect to github-mcp-server via MCP protocol
 * // 2. Send tools/call request with search_code + params
 * // 3. Return result to agent's code
 */
export async function callMcpTool(
  serverName: string,
  toolName: string,
  params: Record<string, any>
): Promise<any> {
  // This function body should NEVER execute in production.
  // The agent harness intercepts this call before it runs.
  //
  // If you see this error, it means:
  // - The code is running outside an agent harness
  // - You need to implement your own harness that intercepts callMcpTool
  
  throw new Error(
    `callMcpTool was not intercepted by agent harness.\n\n` +
    `Attempted: ${serverName}.${toolName}\n` +
    `Params: ${JSON.stringify(params, null, 2)}\n\n` +
    `This function must be intercepted by an agent harness that:\n` +
    `1. Hooks into the execution environment\n` +
    `2. Intercepts callMcpTool() calls\n` +
    `3. Translates them to MCP protocol requests\n` +
    `4. Returns results to the executing code\n\n` +
    `See: docs/code-execution-with-mcp.md for implementation details.`
  );
}
