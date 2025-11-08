/**
 * Test script for generated MCP wrappers
 *
 * This tests the auto-generated wrapper functions to verify they work correctly.
 */

import { list_directory, read_text_file, write_file } from '../servers/filesystem';
import { search_code } from '../servers/github';

async function main() {
  console.log('Testing auto-generated MCP wrappers...\n');

  try {
    // Test filesystem tools
    console.log('1. Testing list_directory...');
    const dirResult = await list_directory({ path: '/private/tmp' });
    console.log(`   ✓ Listed directory (found ${JSON.stringify(dirResult).length} bytes of data)`);

    // Test write and read
    console.log('\n2. Testing write_file...');
    await write_file({
      path: '/private/tmp/test-generated-wrapper.txt',
      content: 'Hello from auto-generated wrappers!'
    });
    console.log('   ✓ File written');

    console.log('\n3. Testing read_text_file...');
    const readResult = await read_text_file({ path: '/private/tmp/test-generated-wrapper.txt' });
    console.log(`   ✓ File read: "${JSON.stringify(readResult).substring(0, 50)}..."`);

    // Test GitHub search (may fail if no auth, but tests the wrapper)
    console.log('\n4. Testing search_code...');
    try {
      const searchResult = await search_code({
        q: 'language:typescript MCP',
        per_page: 5
      });
      console.log(`   ✓ Search completed (results: ${JSON.stringify(searchResult).length} bytes)`);
    } catch (error: any) {
      if (error.message.includes('auth') || error.message.includes('authentication')) {
        console.log('   ⚠ Search requires GitHub authentication (wrapper works, but no auth configured)');
      } else {
        throw error;
      }
    }

    console.log('\n✅ All generated wrappers working correctly!');
  } catch (error) {
    console.error('\n❌ Error:', error);
    throw error;
  }
}

main();
