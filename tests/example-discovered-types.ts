/**
 * Example: Using Discovered Types with Defensive Coding
 * 
 * Demonstrates how to combine TypeScript type hints from schema discovery
 * with runtime defensive coding patterns for robust scripts.
 * 
 * Run: npm run exec tests/example-discovered-types.ts
 */

import { wit_get_work_item, search_workitem } from '../servers/ado';
import type { WitGetWorkItemResult, SearchWorkitemResult } from '../servers/ado/discovered-types';

async function main() {
  try {
    console.log('\n=== Example: Using Discovered Types ===\n');

    // Example 1: Type-safe work item fetch with defensive coding
    console.log('1. Fetching work item with discovered types...');
    
    const workItemResponse = await wit_get_work_item({
      id: 2421643,
      project: 'Secure Cloud Access',
      expand: 'relations'
    });
    
    // Cast to discovered type for IntelliSense support
    const workItem = workItemResponse as WitGetWorkItemResult;
    
    // Defensive access - fields might be undefined
    const title = workItem.fields?.['System.Title'] || 'Untitled';
    const workItemType = workItem.fields?.['System.WorkItemType'] || 'Unknown';
    const state = workItem.fields?.['System.State'] || 'Unknown';
    const parentId = workItem.fields?.['System.Parent']; // May be undefined
    
    console.log(`  ✓ Work Item ${workItem.id}: ${title}`);
    console.log(`    Type: ${workItemType}, State: ${state}`);
    console.log(`    Parent: ${parentId || 'None'}`);
    
    // Safe access to relations array
    const relations = workItem.relations || [];
    const childCount = relations.filter(r => r.rel === 'System.LinkTypes.Hierarchy-Forward').length;
    console.log(`    Children: ${childCount}`);

    // Example 2: Type-safe search with defensive coding
    console.log('\n2. Searching work items with discovered types...');
    
    const searchResponse = await search_workitem({
      searchText: 'user story',
      project: ['Secure Cloud Access'],
      top: 3
    });
    
    // Cast to discovered type
    const searchResult = searchResponse as SearchWorkitemResult;
    
    // Defensive array access
    const results = searchResult.results || [];
    console.log(`  ✓ Found ${searchResult.count || 0} total matches (showing ${results.length})`);
    
    // Process each result with defensive coding
    results.forEach((result, index) => {
      // After normalization: System.Id, System.Workitemtype (note: lowercase 'itemtype')
      const id = result.fields?.['System.Id'] || 'Unknown';
      const type = result.fields?.['System.Workitemtype'] || 'Unknown';
      const title = result.fields?.['System.Title'] || 'Untitled';
      
      console.log(`  ${index + 1}. [${id}] ${type}: ${title}`);
    });

    // Example 3: Combining types with complex defensive patterns
    console.log('\n3. Advanced pattern: processing with type safety...');
    
    // Even with types, check for existence before processing
    if (workItem.fields) {
      const tags = workItem.fields['System.Tags'];
      const tagArray = tags ? tags.split(';').map(t => t.trim()).filter(t => t) : [];
      
      if (tagArray.length > 0) {
        console.log(`  ✓ Tags: ${tagArray.join(', ')}`);
      } else {
        console.log('  ✓ No tags');
      }
    }
    
    // Safe nested property access
    const assignedTo = workItem.fields?.['System.AssignedTo'];
    if (assignedTo && typeof assignedTo === 'object') {
      const assigneeName = (assignedTo as any).displayName || 'Unknown';
      console.log(`  ✓ Assigned to: ${assigneeName}`);
    } else {
      console.log('  ✓ Unassigned');
    }

    console.log('\n=== Key Takeaways ===');
    console.log('✓ Use discovered types for IntelliSense and compile-time hints');
    console.log('✓ Always use defensive patterns - types don\'t guarantee runtime values');
    console.log('✓ Optional chaining (?.) and fallback values (||) are essential');
    console.log('✓ Check array existence before using array methods');
    console.log('✓ ADO responses are normalized to PascalCase automatically');
    console.log('');

  } catch (error: any) {
    console.error('\n❌ Error:', error.message || error);
    if (error.stack) {
      console.error('\nStack trace:', error.stack);
    }
    process.exit(1);
  }
}

main().then(() => {
  process.exit(0);
}).catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
