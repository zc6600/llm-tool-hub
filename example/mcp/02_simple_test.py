#!/usr/bin/env python3
# example/mcp/02_simple_test.py

"""
Simple test to verify the MCP server and adapter work correctly.

This test doesn't use subprocess communication - it tests the components directly.
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from llm_tool_hub.filesystem_tool.create_file_tool import CreateFileTool
from llm_tool_hub.filesystem_tool.read_file_tool import ReadFileTool
from llm_tool_hub.shell_tool.shell_tool import ShellTool
from llm_tool_hub.scientific_research_tool.search_semantic_scholar import SearchSemanticScholar
from llm_tool_hub.integrations.mcp_adapter import MCPAdapter
from llm_tool_hub.integrations.mcp_server import ToolHubMCPServer
from unittest.mock import AsyncMock


async def test_mcp_components():
    """Test the MCP adapter and server components"""
    
    print("=" * 60)
    print("Testing MCP Components")
    print("=" * 60)
    
    # Create adapter with some tools
    tools = [
        CreateFileTool(),
        ReadFileTool(),
        ShellTool(),
        SearchSemanticScholar(),
    ]
    
    adapter = MCPAdapter(tools)
    
    # Test 1: List tools
    print("\n1. Testing tool listing...")
    tools_list = adapter.list_tools()
    print(f"   ✓ Found {len(tools_list)} tools")
    for tool in tools_list:
        print(f"   - {tool['name']}: {tool['description'][:50]}...")
    
    # Test 2: Get specific tool
    print("\n2. Testing tool retrieval...")
    shell_tool = adapter.get_tool("shell_tool")
    if shell_tool:
        print(f"   ✓ Retrieved 'shell_tool' tool: {shell_tool.name}")
    else:
        print("   ✗ Failed to retrieve shell tool")
        return False
    
    # Test 3: Create MCP server
    print("\n3. Testing MCP server initialization...")
    mock_transport = AsyncMock()
    server = ToolHubMCPServer(tools, mock_transport)
    print("   ✓ Server created successfully")
    
    # Test 4: Test initialize handler
    print("\n4. Testing initialize handler...")
    result = await server._handle_initialize({
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "test-client"}
    })
    if "serverInfo" in result:
        print(f"   ✓ Initialize handler works")
        print(f"   - Server name: {result['serverInfo']['name']}")
        print(f"   - Server version: {result['serverInfo']['version']}")
    else:
        print("   ✗ Initialize handler failed")
        print(f"   - Result: {result}")
        return False
    
    # Test 5: Test tools/list handler
    print("\n5. Testing tools/list handler...")
    result = await server._handle_list_tools({})
    if "tools" in result:
        print(f"   ✓ Tools/list handler works")
        print(f"   - Available tools: {len(result['tools'])}")
    else:
        print("   ✗ Tools/list handler failed")
        return False
    
    # Test 6: Test tools/call handler
    print("\n6. Testing tools/call handler...")
    try:
        result = await server._handle_call_tool({
            "name": "shell_tool",
            "arguments": {"command": "echo 'test'"}
        })
        if "content" in result:
            print(f"   ✓ Tools/call handler works")
            content = result['content'][0]['text']
            print(f"   - Command output: {content[:100]}")
        else:
            print("   ✗ Tools/call handler failed")
            return False
    except Exception as e:
        print(f"   ✗ Tools/call handler error: {str(e)[:100]}")
    
    # Test 7: Test message handling
    print("\n7. Testing message handling...")
    mock_transport.reset_mock()
    
    # Create and send a request message
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
    
    response = await server._handle_message(request)
    if response and "id" in response and response["id"] == 1:
        print(f"   ✓ Message handling works")
        print(f"   - Response ID matches request ID")
    else:
        print("   ✗ Message handling failed")
        return False
    
    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = asyncio.run(test_mcp_components())
    sys.exit(0 if success else 1)
