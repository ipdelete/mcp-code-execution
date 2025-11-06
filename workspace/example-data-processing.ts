/**
 * Example: Context-Efficient Data Processing with MCP
 *
 * This demonstrates the pattern from "Code Execution with MCP" where:
 * 1. Import MCP tools as TypeScript modules
 * 2. Fetch large data from MCP servers
 * 3. Process data locally (stays in execution environment)
 * 4. Save full results to disk
 * 5. Return only summary to model context
 *
 * Without code execution:
 *   - Tool definitions for all servers loaded into context (~100KB)
 *   - File contents flow through model context (~50KB)
 *   - Total: ~150KB tokens
 *
 * With code execution:
 *   - Import only needed tools dynamically (~1KB)
 *   - Process data locally
 *   - Return only summary (~100 bytes)
 *   - Total: ~1.1KB tokens (98.5% reduction!)
 */

import { callMcpTool } from '../runtime/mcp-client';
import * as fs from 'fs/promises';
import * as path from 'path';

interface DirectoryListing {
  files: string[];
  directories: string[];
  total: number;
}

async function main() {
  console.log('Demonstrating context-efficient data processing with MCP\n');

  try {
    // Step 1: Fetch data from MCP server
    console.log('Fetching directory listing from filesystem MCP server...');
    const rawResult = await callMcpTool<string>(
      'filesystem__list_directory',
      { path: '/private/tmp' }
    );

    // Step 2: Process data locally (this stays in execution environment)
    console.log('Processing data locally...');
    const lines = rawResult.split('\n').filter(line => line.trim());

    const files: string[] = [];
    const directories: string[] = [];

    for (const line of lines) {
      if (line.startsWith('[FILE]')) {
        files.push(line.substring(7).trim());
      } else if (line.startsWith('[DIR]')) {
        directories.push(line.substring(6).trim());
      }
    }

    const fullResult: DirectoryListing = {
      files,
      directories,
      total: files.length + directories.length
    };

    // Step 3: Save full results to disk
    const outputPath = path.join(process.cwd(), 'workspace', 'directory-listing.json');
    await fs.writeFile(outputPath, JSON.stringify(fullResult, null, 2));
    console.log(`Full results saved to: ${outputPath}`);

    // Step 4: Create summary (only this goes to model context!)
    const summary = {
      totalItems: fullResult.total,
      fileCount: files.length,
      directoryCount: directories.length,
      sampleFiles: files.slice(0, 3),
      sampleDirectories: directories.slice(0, 3),
      dataSize: `${(rawResult.length / 1024).toFixed(2)} KB`,
      savedTo: outputPath
    };

    // Step 5: Return only summary
    console.log('\n=== Summary (only this flows through model context) ===');
    console.log(JSON.stringify(summary, null, 2));

    console.log('\n✅ Pattern demonstration complete!');
    console.log(`\nContext savings:`);
    console.log(`  - Raw data size: ${(rawResult.length / 1024).toFixed(2)} KB`);
    console.log(`  - Summary size: ${(JSON.stringify(summary).length)} bytes`);
    console.log(`  - Reduction: ${(((rawResult.length - JSON.stringify(summary).length) / rawResult.length) * 100).toFixed(1)}%`);

  } catch (error) {
    console.error('❌ Error:', error);
    throw error;
  }
}

main();
