#!/usr/bin/env node

import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import transform from 'json-to-ts';
import { callMcpTool } from './mcp-client.js';

interface ToolConfig {
  description: string;
  sampleParams: Record<string, any>;
}

interface ServerConfig {
  description?: string;
  safeTools: Record<string, ToolConfig>;
}

interface DiscoveryConfig {
  servers: Record<string, ServerConfig>;
  options?: {
    makeFieldsOptional?: boolean;
  };
}

const CONFIG_PATH = join(process.cwd(), 'discovery-config.json');
const SERVERS_DIR = join(process.cwd(), 'servers');

async function main() {
  console.log('\nMCP Schema Discovery\n');

  // Check if config exists
  if (!existsSync(CONFIG_PATH)) {
    console.error('❌ discovery-config.json not found!');
    console.error('\nTo get started:');
    console.error('  1. cp discovery-config.example.json discovery-config.json');
    console.error('  2. Edit discovery-config.json with your project names and IDs');
    console.error('  3. Run npm run discover-schemas again\n');
    process.exit(1);
  }

  // Load config
  const config: DiscoveryConfig = JSON.parse(readFileSync(CONFIG_PATH, 'utf-8'));
  const makeFieldsOptional = config.options?.makeFieldsOptional ?? true;

  console.log(`Found ${Object.keys(config.servers).length} server(s) in config\n`);

  // Process each server
  for (const [serverName, serverConfig] of Object.entries(config.servers)) {
    const toolNames = Object.keys(serverConfig.safeTools);
    
    if (toolNames.length === 0) {
      console.log(`Skipping ${serverName} (no safe tools configured)`);
      continue;
    }

    console.log(`Processing ${serverName}...`);
    console.log(`  ${serverConfig.description || 'No description'}`);
    console.log(`  Discovering ${toolNames.length} tool(s)`);

    const discoveredTypes: string[] = [];
    const typeIndex: string[] = [];

    // Discover schema for each tool
    for (const [toolName, toolConfig] of Object.entries(serverConfig.safeTools)) {
      try {
        console.log(`    🔍 ${toolName}...`);
        
        // Call the tool with sample parameters
        const mcpToolName = `${serverName}__${toolName}`;
        const response = await callMcpTool(mcpToolName, toolConfig.sampleParams);
        
        // Extract the actual data (may be wrapped in .value or direct)
        const data = (response as any)?.value || response;
        
        if (!data || (typeof data !== 'object')) {
          console.log(`      ⚠ No valid data returned, skipping`);
          continue;
        }

        // Generate TypeScript interfaces from the response
        const interfaceName = toPascalCase(toolName) + 'Result';
        
        // Prepare data for json-to-ts
        let sampleData = data;
        if (Array.isArray(data) && data.length > 0) {
          sampleData = data[0]; // Use first element as template
        }
        
        let interfaces: string[];
        try {
          interfaces = transform(sampleData, {
            rootName: interfaceName,
          });
        } catch (err: any) {
          console.log(`      ⚠ Could not generate types: ${err.message}`);
          console.log(`         Creating generic type instead`);
          
          // Fallback: create a simple generic type
          const isArray = Array.isArray(data);
          interfaces = [
            `export interface ${interfaceName} {`,
            `  // Auto-generated from actual response`,
            `  // Run discovery again after updating json-to-ts if needed`,
            `  [key: string]: any;`,
            `}`
          ];
          
          if (isArray) {
            interfaces.push(`export type ${interfaceName}Array = ${interfaceName}[];`);
          }
        }

        // Post-process to make fields optional if configured
        const processedInterfaces = interfaces.map((iface: string) => {
          if (makeFieldsOptional) {
            return iface.replace(/:\s+/g, '?: ');
          }
          return iface;
        });

        // Add comment with tool info
        const toolComment = `/**
 * ${toolConfig.description}
 * Generated from: ${toolName}
 * Sample params: ${JSON.stringify(toolConfig.sampleParams, null, 2).replace(/\n/g, '\n * ')}
 */`;

        discoveredTypes.push(toolComment);
        discoveredTypes.push(processedInterfaces.join('\n\n'));
        discoveredTypes.push(''); // blank line between types

        typeIndex.push(interfaceName);
        
        console.log(`      ✓ Generated ${interfaceName}`);
      } catch (error: any) {
        console.log(`      ❌ Failed: ${error.message}`);
        console.log(`         This tool will be skipped. Check your sample parameters.`);
      }
    }

    // Write discovered types to file
    if (discoveredTypes.length > 0) {
      const serverDir = join(SERVERS_DIR, serverName);
      
      // Ensure directory exists
      if (!existsSync(serverDir)) {
        mkdirSync(serverDir, { recursive: true });
      }

      const outputPath = join(serverDir, 'discovered-types.ts');
      
      const fileContent = `// Auto-generated TypeScript types from actual API responses
// Generated: ${new Date().toISOString()}
// DO NOT EDIT - Run 'npm run discover-schemas' to regenerate
//
// Note: All fields are marked as optional (?) because:
// - API responses vary based on parameters, work item types, and permissions
// - Missing fields are common and expected
// - Always use defensive coding patterns (optional chaining, fallbacks)

${discoveredTypes.join('\n')}

// Export all discovered types
export type {
  ${typeIndex.join(',\n  ')}
};
`;

      writeFileSync(outputPath, fileContent, 'utf-8');
      console.log(`  ✅ Wrote ${typeIndex.length} type(s) to ${serverName}/discovered-types.ts\n`);
    } else {
      console.log(`  ⚠ No types discovered for ${serverName}\n`);
    }
  }

  console.log('✨ Schema discovery complete!\n');
  process.exit(0);
}

function toPascalCase(str: string): string {
  return str
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join('');
}

main().catch((error) => {
  console.error('\n❌ Fatal error:', error);
  process.exit(1);
});
