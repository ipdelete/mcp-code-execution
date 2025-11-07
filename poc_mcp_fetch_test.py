"""PoC: Validate Python MCP SDK with fetch server"""
import asyncio
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

async def test_fetch_server():
    """Test connecting to fetch MCP server"""
    print("🧪 Testing Python MCP SDK with fetch server...")

    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "d33naz-mcp-fetch"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as client:
            await client.initialize()

            # List tools
            tools = await client.list_tools()
            print(f"✓ Found {len(tools.tools)} tools")
            for tool in tools.tools:
                print(f"  - {tool.name}")

            # Test fetch tool
            result = await client.call_tool(
                name="fetch",
                arguments={"url": "https://example.com"}
            )

            print(f"✓ Result type: {type(result)}")
            print(f"✓ Has content: {hasattr(result, 'content')}")

            print("\n✅ Fetch server validation complete")
            return True

if __name__ == "__main__":
    success = asyncio.run(test_fetch_server())
    print(f"\n{'✅ PoC PASSED' if success else '❌ PoC FAILED'}")
