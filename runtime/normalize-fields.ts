/**
 * Generic field normalization utilities for MCP server responses
 * 
 * Different MCP servers (or different APIs within the same server) may return
 * field names with inconsistent casing. This module provides normalization
 * strategies to ensure consumer code sees consistent field names.
 */

/**
 * Normalization strategy type
 */
export type NormalizationStrategy = 'none' | 'ado-pascal-case';

/**
 * Configuration for field normalization by server
 */
export const NORMALIZATION_CONFIG: Record<string, NormalizationStrategy> = {
  'ado': 'ado-pascal-case',
  // Add other servers here as needed
  // 'github': 'none',
  // 'filesystem': 'none',
};

/**
 * Normalizes ADO API response field names to consistent PascalCase.
 * 
 * Different ADO REST APIs return field names with different casing:
 * - Search API returns lowercase: 'system.id', 'system.parent'
 * - Work Item APIs return PascalCase: 'System.Id', 'System.Parent'
 * 
 * This function converts all field names to PascalCase for consistency.
 */
function normalizeAdoFields(obj: any): any {
  if (obj === null || obj === undefined) {
    return obj;
  }

  // Handle arrays
  if (Array.isArray(obj)) {
    return obj.map(item => normalizeAdoFields(item));
  }

  // Handle non-object primitives
  if (typeof obj !== 'object') {
    return obj;
  }

  // Handle objects
  const normalized: any = {};

  for (const [key, value] of Object.entries(obj)) {
    // Normalize the key to PascalCase if it looks like an ADO field name
    let normalizedKey = key;
    
    // Convert system.* fields to System.*
    if (key.startsWith('system.')) {
      normalizedKey = 'System.' + key.slice('system.'.length).replace(/^(.)/, c => c.toUpperCase());
    }
    // Convert microsoft.* fields to Microsoft.*
    else if (key.startsWith('microsoft.')) {
      normalizedKey = 'Microsoft.' + key.slice('microsoft.'.length).replace(/^(.)/, c => c.toUpperCase());
    }
    // Convert custom.* fields to Custom.*
    else if (key.startsWith('custom.')) {
      normalizedKey = 'Custom.' + key.slice('custom.'.length).replace(/^(.)/, c => c.toUpperCase());
    }
    // Convert wef_* fields to WEF_*
    else if (key.toLowerCase().startsWith('wef_')) {
      normalizedKey = 'WEF_' + key.slice(4);
    }

    // Recursively normalize nested objects and arrays
    normalized[normalizedKey] = normalizeAdoFields(value);
  }

  return normalized;
}

/**
 * Main field normalization function
 * Applies the appropriate normalization strategy based on server configuration
 * 
 * @param obj - The response object to normalize
 * @param serverName - The MCP server name (e.g., 'ado', 'github')
 * @returns Normalized object with consistent field names
 */
export function normalizeFieldNames(obj: any, serverName: string): any {
  const strategy = NORMALIZATION_CONFIG[serverName] || 'none';
  
  switch (strategy) {
    case 'ado-pascal-case':
      return normalizeAdoFields(obj);
    case 'none':
    default:
      return obj;
  }
}

/**
 * Extract work item ID from ADO API URL
 * Example: "https://dev.azure.com/.../workItems/123456" -> 123456
 */
export function extractWorkItemIdFromUrl(url: string): number | null {
  const match = url?.match(/workItems\/(\d+)/);
  return match ? parseInt(match[1], 10) : null;
}
