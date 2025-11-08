import { search_repositories, get_file_contents } from '../servers/MCP_DOCKER';

async function main() {
  console.log('Searching for awesome-mcp repositories...\n');

  // Search for awesome-mcp repositories
  const searchResultsRaw = await search_repositories({
    query: 'awesome-mcp in:name,description,readme',
    minimal_output: false,
    perPage: 10
  });

  const results = typeof searchResultsRaw === 'string' ? JSON.parse(searchResultsRaw) : searchResultsRaw;

  if (!results.items || results.items.length === 0) {
    console.log('No awesome-mcp repositories found.');
    return;
  }

  // Get the most popular one
  const topRepo = results.items[0];

  console.log(`Found ${results.total_count} repositories`);
  console.log(`Top result: ${topRepo.full_name} (${topRepo.stargazers_count} stars)\n`);

  // Try to get the README
  let readme = '';
  try {
    const readmeContentRaw = await get_file_contents({
      owner: topRepo.owner.login,
      repo: topRepo.name,
      path: 'README.md'
    });
    const readmeContent = typeof readmeContentRaw === 'string' ? JSON.parse(readmeContentRaw) : readmeContentRaw;
    readme = readmeContent.content;
  } catch (error) {
    console.log('Could not fetch README');
  }

  // Create summary for Obsidian
  const summary = `# Awesome MCP Resources

**Repository:** [${topRepo.full_name}](${topRepo.html_url})

## Overview

${topRepo.description || 'A curated list of awesome MCP (Model Context Protocol) resources'}

## Statistics

- **Stars:** ${topRepo.stargazers_count.toLocaleString()} ⭐
- **Forks:** ${topRepo.forks_count.toLocaleString()}
- **Language:** ${topRepo.language || 'N/A'}
- **Open Issues:** ${topRepo.open_issues_count}

## Timeline

- **Created:** ${new Date(topRepo.created_at).toLocaleDateString()}
- **Last Updated:** ${new Date(topRepo.updated_at).toLocaleDateString()}

## Repository Details

${readme ? '### README Preview\n\n' + readme.split('\n').slice(0, 50).join('\n') + '\n\n*(Truncated - see full README at repository link)*' : ''}

## Other Notable Repositories

${results.items.slice(1, 6).map((repo: any, idx: number) =>
  `${idx + 2}. **[${repo.full_name}](${repo.html_url})** (${repo.stargazers_count} stars)\n   - ${repo.description || 'No description'}`
).join('\n\n')}

## Tags

#mcp #model-context-protocol #resources #awesome-list #ai

---
*Generated via MCP_DOCKER GitHub tools on ${new Date().toLocaleDateString()}*
`;

  // Write to Obsidian
  console.log('Writing to Obsidian 0. Inbox folder...\n');

  const { obsidian_append_content } = await import('../servers/MCP_DOCKER');

  const result = await obsidian_append_content({
    filepath: '0. Inbox/Awesome MCP Resources.md',
    content: summary
  });

  console.log('✅ Successfully wrote awesome-mcp summary to Obsidian!');
  console.log('Result:', result);
}

main();
