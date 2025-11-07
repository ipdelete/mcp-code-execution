#!/usr/bin/env node
/**
 * Auto-generate TypeScript wrapper functions for MCP servers
 *
 * This script connects to all configured MCP servers, discovers their tools,
 * and generates typed TypeScript wrapper functions with proper interfaces.
 */

import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import * as fs from 'fs/promises';
import * as path from 'path';
import { NORMALIZATION_CONFIG } from './normalize-fields.js';

interface ServerConfig {
  command: string;
  args: string[];
  env?: Record<string, string>;
}

interface McpConfig {
  mcpServers: Record<string, ServerConfig>;
}

interface Tool {
  name: string;
  description?: string;
  inputSchema?: {
    type: string;
    properties?: Record<string, any>;
    required?: string[];
  };
  outputSchema?: {
    type: string;
    properties?: Record<string, any>;
    required?: string[];
  };
}

/**
 * Convert JSON Schema type to TypeScript type
 */
function jsonSchemaToTypeScript(schema: any, required: boolean = false): string {
  if (!schema) {
    return 'any';
  }

  // Handle type array (e.g., ["string", "null"])
  if (Array.isArray(schema.type)) {
    const types = schema.type.map((t: string) => {
      if (t === 'null') return 'null';
      return jsonSchemaToTypeScript({ ...schema, type: t }, required);
    });
    return types.join(' | ');
  }

  const type = schema.type;

  // Handle enum
  if (schema.enum) {
    const enumValues = schema.enum.map((v: any) =>
      typeof v === 'string' ? `'${v}'` : String(v)
    );
    return enumValues.join(' | ');
  }

  // Handle basic types
  switch (type) {
    case 'string':
      return 'string';
    case 'number':
    case 'integer':
      return 'number';
    case 'boolean':
      return 'boolean';
    case 'null':
      return 'null';
    case 'array':
      if (schema.items) {
        const itemType = jsonSchemaToTypeScript(schema.items, true);
        return `Array<${itemType}>`;
      }
      return 'any[]';
    case 'object':
      if (schema.properties) {
        return generateInterface(schema, 'inline');
      }
      if (schema.additionalProperties) {
        const valueType = jsonSchemaToTypeScript(schema.additionalProperties, true);
        return `Record<string, ${valueType}>`;
      }
      return 'Record<string, any>';
    default:
      return 'any';
  }
}

/**
 * Generate TypeScript interface from JSON Schema
 */
function generateInterface(schema: any, interfaceName: string): string {
  if (!schema.properties) {
    return '{}';
  }

  const properties = Object.entries(schema.properties).map(([key, propSchema]: [string, any]) => {
    const isRequired = schema.required?.includes(key) || false;
    const typeStr = jsonSchemaToTypeScript(propSchema, isRequired);
    const optional = isRequired ? '' : '?';

    // Add description as comment if available
    const comment = propSchema.description
      ? `  /** ${propSchema.description} */\n  `
      : '  ';

    return `${comment}${key}${optional}: ${typeStr};`;
  });

  if (interfaceName === 'inline') {
    return `{\n${properties.join('\n')}\n}`;
  }

  return properties.join('\n  ');
}

/**
 * Generate result interface from outputSchema if available
 */
function generateResultInterface(tool: Tool): string {
  const resultInterfaceName = toPascalCase(tool.name) + 'Result';
  const lines: string[] = [];

  lines.push(`interface ${resultInterfaceName} {`);
  
  // Use outputSchema if available!
  if (tool.outputSchema?.properties) {
    console.log(`    ✓ Using outputSchema for ${tool.name}`);
    lines.push(generateInterface(tool.outputSchema, resultInterfaceName));
  } else {
    // Generic fallback for servers without outputSchema
    console.log(`    ⚠ No outputSchema for ${tool.name} - using generic type`);
    lines.push('  // No outputSchema provided - response structure may vary');
    lines.push('  // Use defensive coding: const data = response.value || response;');
    lines.push('  value?: any;');
    lines.push('  [key: string]: any;');
  }
  
  lines.push('}');
  return lines.join('\n');
}

/**
 * Generate JSDoc comment from tool description
 */
function generateJSDoc(tool: Tool, paramsInterfaceName: string): string {
  const lines: string[] = ['/**'];

  if (tool.description) {
    // Split long descriptions into multiple lines
    const descLines = tool.description.split('\n');
    descLines.forEach(line => {
      lines.push(` * ${line}`);
    });
  } else {
    lines.push(` * Call the ${tool.name} tool`);
  }

  lines.push(' *');
  
  // Add response structure hint
  if (tool.outputSchema?.properties) {
    lines.push(` * @returns Typed result based on MCP outputSchema`);
  } else {
    lines.push(` * @returns Result from ${tool.name} (no outputSchema - use defensive coding)`);
    lines.push(` * @warning Response structure unknown - always use: const data = response.value || response`);
  }
  
  lines.push(` * @param params - Parameters for ${tool.name}`);
  lines.push(' */');

  return lines.join('\n');
}

/**
 * Generate TypeScript wrapper for a single tool
 */
function generateToolWrapper(serverName: string, tool: Tool): string {
  const functionName = tool.name;
  const paramsInterfaceName = toPascalCase(functionName) + 'Params';
  const resultInterfaceName = toPascalCase(functionName) + 'Result';

  const lines: string[] = [];

  // Import statement
  lines.push("import { callMcpTool } from '../../runtime/mcp-client';");
  
  // Add normalization import for servers that need it
  const needsNormalization = NORMALIZATION_CONFIG[serverName] && NORMALIZATION_CONFIG[serverName] !== 'none';
  if (needsNormalization) {
    lines.push("import { normalizeFieldNames } from '../../runtime/normalize-fields';");
  }
  
  lines.push('');

  // Generate parameter interface
  if (tool.inputSchema?.properties && Object.keys(tool.inputSchema.properties).length > 0) {
    lines.push(`interface ${paramsInterfaceName} {`);
    lines.push(generateInterface(tool.inputSchema, paramsInterfaceName));
    lines.push('}');
    lines.push('');
  } else {
    lines.push(`interface ${paramsInterfaceName} {}`);
    lines.push('');
  }

  // Generate result interface
  lines.push(generateResultInterface(tool));
  lines.push('');

  // Generate JSDoc
  lines.push(generateJSDoc(tool, paramsInterfaceName));

  // Generate function with defensive unwrapping
  const toolIdentifier = `${serverName}__${functionName}`;
  lines.push(`export async function ${functionName}(params: ${paramsInterfaceName}): Promise<${resultInterfaceName}> {`);
  
  // Check if this server needs field normalization
  const serverNeedsNormalization = NORMALIZATION_CONFIG[serverName] && NORMALIZATION_CONFIG[serverName] !== 'none';
  
  if (!tool.outputSchema?.properties) {
    // Add defensive unwrapping for tools without outputSchema
    lines.push(`  const response = await callMcpTool<${resultInterfaceName}>('${toolIdentifier}', params);`);
    lines.push(`  // Defensive unwrapping: handle both wrapped (response.value) and direct responses`);
    const unwrapped = `(response as any)?.value || response`;
    if (serverNeedsNormalization) {
      lines.push(`  const unwrapped = ${unwrapped};`);
      lines.push(`  // Normalize field names to consistent casing`);
      lines.push(`  return normalizeFieldNames(unwrapped, '${serverName}');`);
    } else {
      lines.push(`  return ${unwrapped};`);
    }
  } else {
    if (serverNeedsNormalization) {
      lines.push(`  const response = await callMcpTool<${resultInterfaceName}>('${toolIdentifier}', params);`);
      lines.push(`  // Normalize field names to consistent casing`);
      lines.push(`  return normalizeFieldNames(response, '${serverName}');`);
    } else {
      lines.push(`  return await callMcpTool<${resultInterfaceName}>('${toolIdentifier}', params);`);
    }
  }
  
  lines.push('}');
  lines.push('');

  return lines.join('\n');
}

/**
 * Convert snake_case to PascalCase
 */
function toPascalCase(str: string): string {
  return str
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join('');
}

/**
 * Generate index.ts that exports all tools for a server
 */
function generateIndex(tools: Tool[]): string {
  const lines: string[] = [];

  tools.forEach(tool => {
    lines.push(`export * from './${tool.name}';`);
  });
  
  // Always export utils if it exists
  lines.push(`export * from './utils';`);
  lines.push('');
  return lines.join('\n');
}

/**
 * Generate README with tool documentation
 */
function generateServerReadme(serverName: string, tools: Tool[]): string {
  const lines: string[] = [];
  
  lines.push(`# ${serverName} MCP Tools`);
  lines.push('');
  lines.push(`Auto-generated TypeScript wrappers for ${serverName} MCP server.`);
  lines.push('');
  
  // Count tools with outputSchema for reporting
  const toolsWithOutputSchema = tools.filter(t => t.outputSchema?.properties).length;
  if (toolsWithOutputSchema > 0) {
    lines.push(`**Type Safety:** ${toolsWithOutputSchema}/${tools.length} tools have fully-typed results via outputSchema.`);
    lines.push('');
  }
  
  lines.push(`## Tools (${tools.length})`);
  lines.push('');
  
  // Group tools by category (based on name prefix)
  const categories = new Map<string, Tool[]>();
  tools.forEach(tool => {
    const prefix = tool.name.split('_')[0];
    if (!categories.has(prefix)) {
      categories.set(prefix, []);
    }
    categories.get(prefix)!.push(tool);
  });
  
  // List tools by category
  for (const [category, categoryTools] of categories) {
    lines.push(`### ${category.toUpperCase()}`);
    lines.push('');
    
    categoryTools.forEach(tool => {
      const typeSafe = tool.outputSchema?.properties ? ' ✓' : '';
      lines.push(`- \`${tool.name}()\`${typeSafe}`);
      if (tool.description) {
        const shortDesc = tool.description.split('\n')[0];
        if (shortDesc.length < 100) {
          lines.push(`  - ${shortDesc}`);
        }
      }
    });
    lines.push('');
  }
  
  lines.push('## Usage');
  lines.push('');
  lines.push('```typescript');
  lines.push(`import { ${tools[0]?.name || 'tool_name'} } from '../servers/${serverName}';`);
  lines.push('');
  lines.push(`const result = await ${tools[0]?.name || 'tool_name'}({ /* params */ });`);
  lines.push('```');
  lines.push('');
  
  return lines.join('\n');
}

/**
 * Generate utils.ts template
 */
function generateUtilsTemplate(serverName: string): string {
  const lines: string[] = [];
  
  lines.push('/**');
  lines.push(` * Utility functions for working with ${serverName} MCP responses`);
  lines.push(' */');
  lines.push('');
  lines.push('/**');
  lines.push(' * Normalize response to always return an array.');
  lines.push(' * Handles both direct arrays and value-wrapped responses.');
  lines.push(' * ');
  lines.push(' * @example');
  lines.push(' * const items = toArray(await some_tool({ ... }));');
  lines.push(' */');
  lines.push('export function toArray<T>(response: T[] | { value: T[] } | any): T[] {');
  lines.push('  if (Array.isArray(response)) {');
  lines.push('    return response;');
  lines.push('  }');
  lines.push('  if (response && typeof response === \'object\' && \'value\' in response && Array.isArray(response.value)) {');
  lines.push('    return response.value;');
  lines.push('  }');
  lines.push('  return response as T[];');
  lines.push('}');
  lines.push('');
  
  return lines.join('\n');
}

/**
 * Connect to an MCP server and get its tools
 */
async function getServerTools(serverName: string, config: ServerConfig): Promise<Tool[]> {
  console.log(`Connecting to ${serverName}...`);

  try {
    const transport = new StdioClientTransport({
      command: config.command,
      args: config.args,
      env: {
        ...(process.env as Record<string, string>),
        ...config.env,
      },
    });

    const client = new Client({
      name: 'mcp-wrapper-generator',
      version: '1.0.0',
    }, {
      capabilities: {
        tools: {},
      },
    });

    await client.connect(transport);

    const toolsResult = await client.listTools();
    console.log(`  Found ${toolsResult.tools.length} tools`);

    await client.close();

    return toolsResult.tools;
  } catch (error) {
    console.error(`  Failed to connect to ${serverName}:`, error);
    return [];
  }
}

/**
 * Main generation function
 */
export async function generateWrappers() {
  console.log('MCP Wrapper Generator\n');

  // Load config
  const configPath = path.join(process.cwd(), 'mcp-config.json');
  let config: McpConfig;

  try {
    const configContent = await fs.readFile(configPath, 'utf-8');
    config = JSON.parse(configContent);
  } catch (error) {
    console.error(`Failed to load ${configPath}:`, error);
    process.exit(1);
  }

  if (!config.mcpServers) {
    console.error('Invalid config: missing mcpServers');
    process.exit(1);
  }

  console.log(`Found ${Object.keys(config.mcpServers).length} servers in config\n`);

  // Process each server
  for (const [serverName, serverConfig] of Object.entries(config.mcpServers)) {
    const tools = await getServerTools(serverName, serverConfig);

    if (tools.length === 0) {
      console.log(`  Skipping ${serverName} (no tools)\n`);
      continue;
    }

    // Count tools with outputSchema
    const toolsWithOutputSchema = tools.filter(t => t.outputSchema?.properties).length;
    console.log(`  Tools with outputSchema: ${toolsWithOutputSchema}/${tools.length}`);

    // Create server directory
    const serverDir = path.join(process.cwd(), 'servers', serverName);
    await fs.mkdir(serverDir, { recursive: true });

    // Generate wrapper for each tool
    console.log(`  Generating wrappers...`);
    for (const tool of tools) {
      const wrapperCode = generateToolWrapper(serverName, tool);
      const wrapperPath = path.join(serverDir, `${tool.name}.ts`);
      await fs.writeFile(wrapperPath, wrapperCode);
      console.log(`    ✓ ${tool.name}.ts`);
    }

    // Generate index.ts
    const indexCode = generateIndex(tools);
    const indexPath = path.join(serverDir, 'index.ts');
    await fs.writeFile(indexPath, indexCode);
    console.log(`    ✓ index.ts`);
    
    // Generate README.md
    const readmeCode = generateServerReadme(serverName, tools);
    const readmePath = path.join(serverDir, 'README.md');
    await fs.writeFile(readmePath, readmeCode);
    console.log(`    ✓ README.md`);
    
    // Generate utils.ts (only if it doesn't exist)
    const utilsPath = path.join(serverDir, 'utils.ts');
    try {
      await fs.access(utilsPath);
      console.log(`    ⊙ utils.ts (preserved)`);
    } catch {
      // File doesn't exist, create template
      const utilsTemplate = generateUtilsTemplate(serverName);
      await fs.writeFile(utilsPath, utilsTemplate);
      console.log(`    ✓ utils.ts (created)`);
    }
    
    console.log('');
  }

  console.log('✨ Wrapper generation complete!');
}

// Run if called directly (auto-execute when run as a script)
generateWrappers().catch(error => {
  console.error('Generation failed:', error);
  process.exit(1);
});
