#!/usr/bin/env python3
# example/mcp/01_basic_stdio_server.py

"""
Minimal MCP Server Example

This example demonstrates how to create a basic MCP server using llm-tool-hub.
The server exposes various tools through the Model Context Protocol.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the src directory to the path so we can import llm_tool_hub
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from llm_tool_hub.filesystem_tool.create_file_tool import CreateFileTool
from llm_tool_hub.filesystem_tool.read_file_tool import ReadFileTool
from llm_tool_hub.filesystem_tool.modify_file_tool import ModifyFileTool
from llm_tool_hub.shell_tool.shell_tool import ShellTool
from llm_tool_hub.scientific_research_tool.search_semantic_scholar import SearchSemanticScholar
from llm_tool_hub.integrations.mcp_adapter import MCPAdapter
from llm_tool_hub.transports.stdio_transport import StdioTransport
from llm_tool_hub.integrations.mcp_server import ToolHubMCPServer

import asyncio
import logging
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])

from llm_tool_hub.filesystem_tool import CreateFileTool, ReadFileTool, ModifyFileTool
from llm_tool_hub.shell_tool import ShellTool
from llm_tool_hub.scientific_research_tool import SearchSemanticScholar
from llm_tool_hub.integrations.mcp_server import ToolHubMCPServer
from llm_tool_hub.transports.stdio_transport import StdioTransport


def setup_logging():
    """Setup logging to stderr (so stdout is clean for JSON-RPC messages)"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stderr)],
    )


async def main():
    """Start the MCP server"""
    setup_logging()
    
    logger = logging.getLogger(__name__)
    logger.info("Starting llm-tool-hub MCP Server")
    
    # Initialize tools
    tools = [
        CreateFileTool(),
        ReadFileTool(),
        ModifyFileTool(),
        ShellTool(),
        SearchSemanticScholar(),
    ]
    
    logger.info(f"Loaded {len(tools)} tools: {[t.name for t in tools]}")
    
    # Create transport (stdio)
    transport = StdioTransport()
    
    # Create and run server
    server = ToolHubMCPServer(tools, transport)
    
    try:
        await server.run()
    except KeyboardInterrupt:
        logger.info("Server interrupted")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
