import { callMcpTool } from '../../runtime/mcp-client';

interface SearchCodeParams {
  query: string;
  sort?: string;
  order?: 'asc' | 'desc';
  page?: number;
  perPage?: number;
}

interface SearchCodeResult {
  total_count: number;
  incomplete_results: boolean;
  items: Array<{
    name: string;
    path: string;
    sha: string;
    url: string;
    git_url: string;
    html_url: string;
    repository: {
      id: number;
      name: string;
      full_name: string;
      owner: {
        login: string;
      };
    };
    score: number;
    text_matches?: Array<{
      fragment: string;
    }>;
  }>;
}

/**
 * Fast and precise code search across ALL GitHub repositories using GitHub's native search engine.
 * Best for finding exact symbols, functions, classes, or specific code patterns.
 * 
 * @param params - Search parameters
 * @param params.query - Search query using GitHub's code search syntax
 * @param params.sort - Sort field ('indexed' only)
 * @param params.order - Sort order for results ('asc' or 'desc')
 * @param params.page - Page number for pagination (min 1)
 * @param params.perPage - Results per page for pagination (min 1, max 100)
 * @returns Search results with code matches
 * 
 * @example
 * // Search for a specific function in Python
 * const results = await search_code({
 *   query: 'content:Skill language:Python org:github'
 * });
 * 
 * @example
 * // Search within a specific repository
 * const results = await search_code({
 *   query: 'repo:github/github-mcp-server authentication',
 *   perPage: 50
 * });
 */
export async function search_code(params: SearchCodeParams): Promise<SearchCodeResult> {
  return await callMcpTool<SearchCodeResult>('github__search_code', params);
}
