#!/usr/bin/env node

/**
 * MCP Code Execution Harness
 * Executes TypeScript scripts with on-demand MCP server connections.
 */

import { register } from 'tsx/esm/api';
import * as path from 'path';
import * as fs from 'fs';
import { pathToFileURL } from 'url';
import { getMcpClientManager } from './mcp-client.js';

async function main() {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.error('Usage: npm run exec <script.ts>');
    process.exit(1);
  }

  const scriptPath = path.resolve(process.cwd(), args[0]);

  if (!fs.existsSync(scriptPath)) {
    console.error(`Error: Script not found: ${scriptPath}`);
    process.exit(1);
  }

  // Initialize MCP client manager
  const manager = getMcpClientManager();
  await manager.initialize();

  // Handle cleanup on exit
  const cleanup = async () => {
    await manager.cleanup();
    process.exit(0);
  };

  process.on('SIGINT', cleanup);
  process.on('SIGTERM', cleanup);

  // Register tsx and execute script
  register();

  try {
    await import(pathToFileURL(scriptPath).href);
  } catch (error) {
    console.error('Script execution failed:', error);
    process.exit(1);
  } finally {
    await manager.cleanup();
  }
}

main().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
