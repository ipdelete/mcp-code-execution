/**
 * Test script for MCP code execution pattern
 *
 * This demonstrates the pattern from the article where:
 * 1. Import MCP tools as TypeScript modules
 * 2. Call tools via callMcpTool (intercepted by harness)
 * 3. Process data locally without passing through context
 * 4. Return only summary
 */

import { callMcpTool } from '../servers/mcp-client';

async function main() {
  console.log('Testing MCP code execution pattern...\n');

  try {
    // Call filesystem MCP server to list directory
    console.log('Listing files in /private/tmp...');
    const result = await callMcpTool<{ content: Array<{ type: string, text: string }> }>(
      'filesystem__list_directory',
      { path: '/private/tmp' }
    );

    console.log('Result:', JSON.stringify(result, null, 2));

    console.log('\n✅ MCP code execution pattern working!');
  } catch (error) {
    console.error('❌ Error:', error);
    throw error;
  }
}

main();
