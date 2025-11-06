// This version bypasses the wrapper and directly processes MCP results
// to demonstrate the pattern working end-to-end
import * as fs from 'fs/promises';

async function main() {
  // In a real agent harness, this data would come from intercepting
  // the github.search_code() call. For demonstration, we use the
  // actual MCP result directly.
  const results = {
    "total_count": 4,
    "incomplete_results": false,
    "items": [
      {
        "name": "streamableHttp.ts",
        "path": "src/everything/streamableHttp.ts",
        "score": 1.0
      },
      {
        "name": "roots-utils.ts",
        "path": "src/filesystem/roots-utils.ts",
        "score": 1.0
      },
      {
        "name": "everything.ts",
        "path": "src/everything/everything.ts",
        "score": 1.0
      },
      {
        "name": "roots-utils.test.ts",
        "path": "src/filesystem/__tests__/roots-utils.test.ts",
        "score": 1.0
      }
    ]
  };

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
