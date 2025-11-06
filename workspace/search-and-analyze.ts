import * as github from '../servers/github-mcp';
import * as fs from 'fs/promises';

async function main() {
  // Call GitHub MCP server
  const results = await github.search_code({
    query: 'MCP language:typescript repo:modelcontextprotocol/servers',
    perPage: 100
  });

  // Extract directories (data stays in execution environment)
  const directories = results.items.map(item => 
    item.path.substring(0, item.path.lastIndexOf('/'))
  );

  // Count occurrences
  const dirCounts = directories.reduce((acc, dir) => {
    acc[dir] = (acc[dir] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  // Find top 3
  const topDirectories = Object.entries(dirCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([dir]) => dir);

  // Calculate average score
  const averageScore = results.items.reduce((sum, item) => 
    sum + item.score, 0) / results.items.length;

  // Save full results to disk
  await fs.writeFile(
    './workspace/mcp-files.json', 
    JSON.stringify(results, null, 2)
  );

  // Return only summary (this goes to context)
  const summary = {
    totalFiles: results.items.length,
    topDirectories,
    averageScore
  };
  
  console.log(JSON.stringify(summary, null, 2));
}

main();
