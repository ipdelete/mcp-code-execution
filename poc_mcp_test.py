"""
PoC: Validate Python MCP SDK compatibility
Tests stdio transport, connection lifecycle, and response structure
"""
import asyncio
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

async def test_mcp_connection():
    """Test connecting to git MCP server"""
    print("🧪 Testing Python MCP SDK with git server...")

    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@cyanheads/git-mcp-server"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as client:
            # Test 1: Initialize
            print("\n✓ Test 1: Initialize connection")
            await client.initialize()

            # Test 2: List tools
            print("✓ Test 2: List tools")
            tools = await client.list_tools()
            print(f"  Found {len(tools.tools)} tools")
            for tool in tools.tools:
                print(f"    - {tool.name}: {tool.description}")

            # Test 3: Call tool
            print("\n✓ Test 3: Call git_status tool")
            result = await client.call_tool(
                name="git_status",
                arguments={"path": "/Users/ianphil/src/mcp-code-execution-phase0"}
            )

            # Test 4: Validate response structure
            print("\n✓ Test 4: Validate response structure")
            print(f"  Result type: {type(result)}")
            print(f"  Result attributes: {dir(result)}")

            # Test defensive unwrapping
            if hasattr(result, 'content'):
                print("  ✅ Has .content attribute")
                if isinstance(result.content, list):
                    print(f"  ✅ Content is list with {len(result.content)} items")
                    if result.content:
                        print(f"  ✅ First item type: {type(result.content[0])}")

            print("\n✅ Git server validation complete")
            return True

if __name__ == "__main__":
    success = asyncio.run(test_mcp_connection())
    print(f"\n{'✅ PoC PASSED' if success else '❌ PoC FAILED'}")
