/**
 * Test direct MCP tool call
 */

import { getMcpClientManager } from '../runtime/mcp-client-impl';

async function main() {
  console.log('Initializing MCP client...\n');

  const manager = getMcpClientManager();
  await manager.initialize();

  console.log('Calling filesystem__list_directory...\n');

  try {
    const result = await manager.callTool('filesystem__list_directory', { path: '/private/tmp' });
    console.log('Result:', JSON.stringify(result, null, 2));
  } catch (error) {
    console.error('Error:', error);
  }

  await manager.cleanup();
}

main().catch(console.error);
