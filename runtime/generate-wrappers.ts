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
  lines.push(` * @param params - Parameters for ${tool.name}`);
  lines.push(` * @returns Result from ${tool.name}`);
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

  // Generate result interface (generic for now)
  lines.push(`interface ${resultInterfaceName} {`);
  lines.push('  [key: string]: any;');
  lines.push('}');
  lines.push('');

  // Generate JSDoc
  lines.push(generateJSDoc(tool, paramsInterfaceName));

  // Generate function
  const toolIdentifier = `${serverName}__${functionName}`;
  lines.push(`export async function ${functionName}(params: ${paramsInterfaceName}): Promise<${resultInterfaceName}> {`);
  lines.push(`  return await callMcpTool<${resultInterfaceName}>('${toolIdentifier}', params);`);
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
        ...process.env,
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
async function generateWrappers() {
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
    console.log('');
  }

  console.log('✨ Wrapper generation complete!');
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  generateWrappers().catch(error => {
    console.error('Generation failed:', error);
    process.exit(1);
  });
}
