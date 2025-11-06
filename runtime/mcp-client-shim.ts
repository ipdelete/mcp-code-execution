/**
 * MCP Client Shim
 *
 * This file replaces servers/mcp-client.ts when running through the harness.
 * It exports the real MCP implementation instead of stubs.
 */

export { callMcpTool, McpToolResult } from './mcp-client-impl.js';
