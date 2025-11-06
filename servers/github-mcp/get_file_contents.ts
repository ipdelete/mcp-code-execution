import { callMcpTool } from '../mcp-client';

interface GetFileContentsParams {
  owner: string;
  repo: string;
  path?: string;
  ref?: string;
  sha?: string;
}

interface FileContent {
  name: string;
  path: string;
  sha: string;
  size: number;
  url: string;
  html_url: string;
  git_url: string;
  download_url: string;
  type: 'file';
  content: string;
  encoding: 'base64';
}

interface DirectoryContent {
  name: string;
  path: string;
  sha: string;
  size: number;
  url: string;
  html_url: string;
  git_url: string;
  download_url: string | null;
  type: 'dir' | 'file' | 'symlink' | 'submodule';
}

type GetFileContentsResult = FileContent | DirectoryContent[];

/**
 * Get the contents of a file or directory from a GitHub repository.
 * 
 * @param params - Parameters for retrieving file contents
 * @param params.owner - Repository owner (username or organization)
 * @param params.repo - Repository name
 * @param params.path - Path to file/directory (directories must end with a slash '/')
 * @param params.ref - Optional git refs such as `refs/tags/{tag}`, `refs/heads/{branch}` or `refs/pull/{pr_number}/head`
 * @param params.sha - Optional commit SHA. If specified, it will be used instead of ref
 * @returns File contents (base64 encoded) or directory listing
 * 
 * @example
 * // Get contents of a specific file
 * const fileContent = await get_file_contents({
 *   owner: 'github',
 *   repo: 'github-mcp-server',
 *   path: 'README.md'
 * });
 * 
 * @example
 * // List contents of a directory
 * const dirContents = await get_file_contents({
 *   owner: 'github',
 *   repo: 'github-mcp-server',
 *   path: 'src/'
 * });
 * 
 * @example
 * // Get file from a specific branch
 * const fileContent = await get_file_contents({
 *   owner: 'github',
 *   repo: 'github-mcp-server',
 *   path: 'package.json',
 *   ref: 'refs/heads/main'
 * });
 */
export async function get_file_contents(params: GetFileContentsParams): Promise<GetFileContentsResult> {
  return await callMcpTool('github-mcp-server', 'get_file_contents', params);
}
