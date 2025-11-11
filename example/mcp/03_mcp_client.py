#!/usr/bin/env python3
# example/mcp/03_mcp_client.py

"""
Simple MCP client for testing the server.

This client sends JSON-RPC requests to an MCP server and prints responses.

Usage:
    # Terminal 1: Start the server
    python 01_basic_stdio_server.py

    # Terminal 2: Run the client
    python 03_mcp_client.py

This will:
1. Send initialize request
2. List available tools
3. Call a simple tool
"""

import asyncio
import json
import sys
import subprocess
from typing import Any, Dict, Optional


class MCPClient:
    """Simple MCP client for communicating with stdio-based MCP servers"""

    def __init__(self, server_command: str):
        """
        Initialize the client.
        
        Args:
            server_command: Command to start the server (e.g., "python server.py")
        """
        self.server_process: Optional[subprocess.Popen] = None
        self.server_command = server_command
        self.request_id = 0

    async def start_server(self):
        """Start the MCP server process"""
        print(f"Starting server: {self.server_command}")
        self.server_process = subprocess.Popen(
            self.server_command,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        print("Server started")

    async def stop_server(self):
        """Stop the MCP server process"""
        if self.server_process:
            self.server_process.stdin.close()
            self.server_process.wait(timeout=5)
            print("Server stopped")

    async def send_request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send a request to the server and get the response.
        
        Args:
            method: JSON-RPC method name
            params: Method parameters
            
        Returns:
            Response dict
        """
        if not self.server_process or not self.server_process.stdin:
            raise RuntimeError("Server not started")
        
        self.request_id += 1
        
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {},
        }
        
        print(f"\n→ Sending: {method}")
        request_json = json.dumps(request)
        self.server_process.stdin.write(request_json + "\n")
        self.server_process.stdin.flush()
        
        # Read response
        response_line = self.server_process.stdout.readline()
        if not response_line:
            raise RuntimeError("No response from server")
        
        response = json.loads(response_line)
        
        print(f"← Received: {json.dumps(response, indent=2)}")
        
        return response

    async def list_tools(self) -> list:
        """List available tools"""
        response = await self.send_request("tools/list")
        return response.get("result", {}).get("tools", [])

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Call a tool"""
        response = await self.send_request(
            "tools/call",
            {"name": name, "arguments": arguments}
        )
        
        result = response.get("result", {})
        content = result.get("content", [])
        if content:
            return content[0].get("text", "")
        return ""


async def main():
    """Run the client test"""
    client = MCPClient("python 01_basic_stdio_server.py")
    
    try:
        # Start server
        await client.start_server()
        await asyncio.sleep(1)  # Give server time to start
        
        # Initialize
        print("\n" + "="*60)
        print("1. INITIALIZE REQUEST")
        print("="*60)
        await client.send_request("initialize", {"clientInfo": {"name": "test-client"}})
        
        # List tools
        print("\n" + "="*60)
        print("2. LIST TOOLS REQUEST")
        print("="*60)
        tools = await client.list_tools()
        print(f"\nFound {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description']}")
        
        # Call a tool (if SearchSemanticScholar is available)
        semantic_scholar_tool = next(
            (t for t in tools if t["name"] == "search_semantic_scholar"),
            None
        )
        
        if semantic_scholar_tool:
            print("\n" + "="*60)
            print("3. CALL TOOL REQUEST (SearchSemanticScholar)")
            print("="*60)
            result = await client.call_tool(
                "search_semantic_scholar",
                {"query": "deep learning", "limit": 2}
            )
            print(f"\nTool result:\n{result[:200]}...")  # Print first 200 chars
        
        print("\n" + "="*60)
        print("✓ Test completed successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
    finally:
        await client.stop_server()


if __name__ == "__main__":
    asyncio.run(main())
