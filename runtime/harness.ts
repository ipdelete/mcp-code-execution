#!/usr/bin/env node

/**
 * MCP Code Execution Harness
 *
 * This harness executes TypeScript code with MCP tool call interception.
 * It implements the pattern from "Code Execution with MCP" where:
 *
 * 1. Agent writes code that imports from ./servers/
 * 2. Code calls callMcpTool() from servers/mcp-client
 * 3. Harness intercepts and routes to real MCP implementation
 * 4. Results flow back as if the function executed normally
 */

import { register } from 'tsx/esm/api';
import * as path from 'path';
import * as fs from 'fs';
import { pathToFileURL } from 'url';
import { getMcpClientManager } from './mcp-client-impl.js';

/**
 * Setup module interception for callMcpTool
 */
function setupInterception() {
  const Module = require('module');
  const originalRequire = Module.prototype.require;

  Module.prototype.require = function (id: string) {
    // Intercept imports of servers/mcp-client
    if (id.includes('servers/mcp-client') || id.includes('../servers/mcp-client')) {
      // Return our real implementation instead of the stub
      const mcpClientImpl = require('./mcp-client-impl');
      return {
        callMcpTool: mcpClientImpl.callMcpTool,
        McpToolResult: undefined,
      };
    }

    // For all other requires, use the original
    return originalRequire.apply(this, arguments);
  };
}

async function main() {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.error('Usage: npm run exec <script.ts>');
    console.error('');
    console.error('Example:');
    console.error('  npm run exec workspace/search-and-analyze.ts');
    process.exit(1);
  }

  const scriptPath = path.resolve(process.cwd(), args[0]);

  // Check if script exists
  if (!fs.existsSync(scriptPath)) {
    console.error(`Error: Script not found: ${scriptPath}`);
    process.exit(1);
  }

  // Set environment variable to indicate harness is active
  process.env.MCP_HARNESS_ACTIVE = 'true';

  console.error(`[Harness] Initializing MCP client manager...`);

  // Initialize MCP client manager
  const manager = getMcpClientManager();
  try {
    await manager.initialize();
    console.error(`[Harness] MCP client manager initialized`);
  } catch (error) {
    console.error(`[Harness] Failed to initialize MCP client manager:`, error);
    process.exit(1);
  }

  console.error(`[Harness] Executing script: ${scriptPath}`);
  console.error(`[Harness] ---`);

  // Register tsx for TypeScript execution
  register();

  try {
    // Import and execute the script
    const scriptUrl = pathToFileURL(scriptPath).href;
    await import(scriptUrl);
  } catch (error) {
    console.error(`[Harness] Script execution failed:`, error);
    process.exit(1);
  } finally {
    // Cleanup
    console.error(`[Harness] ---`);
    console.error(`[Harness] Cleaning up...`);
    await manager.cleanup();
    console.error(`[Harness] Done`);
  }
}

// Handle cleanup on exit
process.on('SIGINT', async () => {
  console.error('\n[Harness] Interrupted, cleaning up...');
  const manager = getMcpClientManager();
  await manager.cleanup();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  console.error('\n[Harness] Terminated, cleaning up...');
  const manager = getMcpClientManager();
  await manager.cleanup();
  process.exit(0);
});

main().catch(error => {
  console.error('[Harness] Fatal error:', error);
  process.exit(1);
});
