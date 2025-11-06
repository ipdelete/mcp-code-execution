/**
 * Simple test to list available MCP tools
 */

import { getMcpClientManager } from '../runtime/mcp-client-impl';

async function main() {
  console.log('Initializing MCP client...\n');

  const manager = getMcpClientManager();
  await manager.initialize();

  console.log('Listing all available tools:\n');
  const tools = await manager.listAllTools();

  for (const { server, tool } of tools) {
    console.log(`${server}__${tool.name}`);
    if (tool.description) {
      console.log(`  ${tool.description}`);
    }
  }

  console.log(`\nTotal: ${tools.length} tools available`);

  await manager.cleanup();
}

main().catch(console.error);
