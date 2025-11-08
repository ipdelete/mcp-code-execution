/**
 * MCP Client Implementation
 *
 * Connects to MCP servers via stdio and provides tool calling functionality.
 * This is the actual implementation that the harness uses to execute MCP calls.
 */

import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { spawn } from 'child_process';
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

export class McpClientManager {
  private clients: Map<string, Client> = new Map();
  private toolCache: Map<string, any[]> = new Map();
  private config: McpConfig | null = null;
  private initialized = false;

  /**
   * Initialize the MCP client manager by loading configuration.
   *
   * IMPORTANT: This does NOT connect to servers upfront. Servers connect
   * lazily on-demand when tools are first called. This implements the
   * "progressive disclosure" pattern from the article where agents discover
   * tools by exploring the filesystem, not loading everything upfront.
   */
  async initialize(configPath?: string): Promise<void> {
    if (this.initialized) {
      return;
    }

    // Load configuration
    const configFile = configPath || path.join(process.cwd(), 'mcp-config.json');
    try {
      const configContent = await fs.readFile(configFile, 'utf-8');
      this.config = JSON.parse(configContent);
    } catch (error) {
      throw new Error(`Failed to load MCP configuration from ${configFile}: ${error}`);
    }

    if (!this.config?.mcpServers) {
      throw new Error('Invalid MCP configuration: missing mcpServers');
    }

    this.initialized = true;
    console.error(`[MCP] Configuration loaded (${Object.keys(this.config.mcpServers).length} servers available)`);
    console.error(`[MCP] Servers will connect on-demand when tools are first called`);
  }

  /**
   * Connect to a single MCP server
   */
  private async connectToServer(serverName: string, config: ServerConfig): Promise<void> {
    try {
      // Create stdio transport
      const transport = new StdioClientTransport({
        command: config.command,
        args: config.args,
        env: {
          ...process.env,
          ...config.env,
        },
      });

      // Create client
      const client = new Client({
        name: 'mcp-code-execution-client',
        version: '1.0.0',
      }, {
        capabilities: {
          tools: {},
        },
      });

      // Connect to server
      await client.connect(transport);

      // Store client
      this.clients.set(serverName, client);

      // Cache available tools
      const toolsResult = await client.listTools();
      this.toolCache.set(serverName, toolsResult.tools);

      console.error(`[MCP] Connected to server: ${serverName} (${toolsResult.tools.length} tools)`);
    } catch (error) {
      console.error(`[MCP] Failed to connect to server ${serverName}:`, error);
      throw error;
    }
  }

  /**
   * Call a tool on a specific MCP server.
   *
   * Implements lazy loading: connects to server on-demand if not already connected.
   * This is the progressive disclosure pattern - only load what you need when you need it.
   */
  async callTool(toolIdentifier: string, params: Record<string, any>): Promise<any> {
    if (!this.initialized) {
      await this.initialize();
    }

    // Parse tool identifier (format: "serverName__toolName")
    const parts = toolIdentifier.split('__');
    if (parts.length !== 2) {
      throw new Error(
        `Invalid tool identifier: ${toolIdentifier}\n` +
        `Expected format: "serverName__toolName" (e.g., "github__search_code")`
      );
    }

    const [serverName, toolName] = parts;

    // Connect to server lazily if not already connected
    if (!this.clients.has(serverName)) {
      const serverConfig = this.config?.mcpServers[serverName];
      if (!serverConfig) {
        throw new Error(
          `MCP server not configured: ${serverName}\n` +
          `Available servers in config: ${Object.keys(this.config?.mcpServers || {}).join(', ')}\n` +
          `Add "${serverName}" to mcp-config.json to use it.`
        );
      }
      console.error(`[MCP] Connecting to server on-demand: ${serverName}`);
      await this.connectToServer(serverName, serverConfig);
    }

    // Get client for this server
    const client = this.clients.get(serverName);
    if (!client) {
      throw new Error(`Failed to get client for server: ${serverName}`);
    }

    // Check if tool exists
    const tools = this.toolCache.get(serverName) || [];
    const tool = tools.find(t => t.name === toolName);
    if (!tool) {
      throw new Error(
        `Tool not found: ${toolName} on server ${serverName}\n` +
        `Available tools: ${tools.map(t => t.name).join(', ')}`
      );
    }

    try {
      // Call the tool
      const result = await client.callTool({
        name: toolName,
        arguments: params,
      });

      // Extract content from result
      if (result.content && Array.isArray(result.content)) {
        if (result.content.length === 1) {
          const content = result.content[0];
          if (content.type === 'text') {
            // Try to parse as JSON if it looks like JSON
            const text = content.text;
            if (text.trim().startsWith('{') || text.trim().startsWith('[')) {
              try {
                return JSON.parse(text);
              } catch {
                return text;
              }
            }
            return text;
          }
          return content;
        }
        return result.content;
      }

      return result;
    } catch (error) {
      throw new Error(`Failed to call tool ${toolName}: ${error}`);
    }
  }

  /**
   * List all available tools across all servers
   */
  async listAllTools(): Promise<Array<{ server: string; tool: any }>> {
    if (!this.initialized) {
      await this.initialize();
    }

    const allTools: Array<{ server: string; tool: any }> = [];
    for (const [serverName, tools] of this.toolCache.entries()) {
      for (const tool of tools) {
        allTools.push({ server: serverName, tool });
      }
    }
    return allTools;
  }

  /**
   * Disconnect from all servers and cleanup
   */
  async cleanup(): Promise<void> {
    const closePromises = Array.from(this.clients.values()).map(client =>
      client.close().catch(err => console.error('[MCP] Error closing client:', err))
    );
    await Promise.all(closePromises);
    this.clients.clear();
    this.toolCache.clear();
    this.initialized = false;
  }
}

// Singleton instance
let managerInstance: McpClientManager | null = null;

/**
 * Get or create the MCP client manager instance
 */
export function getMcpClientManager(): McpClientManager {
  if (!managerInstance) {
    managerInstance = new McpClientManager();
  }
  return managerInstance;
}

/**
 * Call an MCP tool using the identifier pattern from the article
 *
 * @param toolIdentifier - Combined identifier: "serverName__toolName"
 * @param params - Tool parameters
 */
export async function callMcpTool(
  toolIdentifier: string,
  params: Record<string, any>
): Promise<any> {
  const manager = getMcpClientManager();
  return manager.callTool(toolIdentifier, params);
}
