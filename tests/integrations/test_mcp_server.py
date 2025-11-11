# tests/integrations/test_mcp_server.py

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, MagicMock
from llm_tool_hub.integrations.mcp_server import ToolHubMCPServer
from llm_tool_hub.base_tool import BaseTool
from llm_tool_hub.transports.base_transport import BaseTransport


class SimpleTool(BaseTool):
    """Simple test tool"""
    name = "simple"
    description = "Simple test tool"
    parameters = {
        "type": "object",
        "properties": {
            "text": {"type": "string"},
        },
        "required": ["text"],
    }

    def run(self, text: str) -> str:
        return f"Echo: {text}"


class TestToolHubMCPServer:
    """Test suite for ToolHubMCPServer"""

    @pytest.fixture
    def mock_transport(self):
        """Create a mock transport"""
        transport = AsyncMock(spec=BaseTransport)
        transport.start = AsyncMock()
        transport.stop = AsyncMock()
        transport.send = AsyncMock()
        return transport

    @pytest.fixture
    def server(self, mock_transport):
        """Create server with mock transport"""
        return ToolHubMCPServer([SimpleTool()], mock_transport)

    @pytest.mark.asyncio
    async def test_server_initialization(self, server):
        """Test server initialization"""
        assert server.server_name == "llm-tool-hub"
        assert server.adapter.get_tool("simple") is not None

    @pytest.mark.asyncio
    async def test_initialize_handler(self, server):
        """Test initialize request handler"""
        result = await server._handle_initialize({"clientInfo": {"name": "test"}})
        
        assert "serverInfo" in result
        assert result["serverInfo"]["name"] == "llm-tool-hub"
        assert "capabilities" in result

    @pytest.mark.asyncio
    async def test_list_tools_handler(self, server):
        """Test tools/list request handler"""
        result = await server._handle_list_tools({})
        
        assert "tools" in result
        assert len(result["tools"]) == 1
        assert result["tools"][0]["name"] == "simple"

    @pytest.mark.asyncio
    async def test_call_tool_handler(self, server):
        """Test tools/call request handler"""
        result = await server._handle_call_tool({
            "name": "simple",
            "arguments": {"text": "hello"}
        })
        
        assert "content" in result
        assert len(result["content"]) > 0
        assert "Echo: hello" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_call_tool_missing_name(self, server):
        """Test tools/call with missing tool name"""
        with pytest.raises(ValueError):
            await server._handle_call_tool({"arguments": {}})

    @pytest.mark.asyncio
    async def test_call_tool_nonexistent(self, server):
        """Test calling a tool that doesn't exist"""
        with pytest.raises(ValueError):
            await server._handle_call_tool({
                "name": "nonexistent",
                "arguments": {}
            })

    @pytest.mark.asyncio
    async def test_handle_message_initialize(self, server):
        """Test handling an initialize message"""
        message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {}
        }
        
        response = await server._handle_message(message)
        
        assert response["id"] == 1
        assert "result" in response
        assert "serverInfo" in response["result"]

    @pytest.mark.asyncio
    async def test_handle_message_list_tools(self, server):
        """Test handling a tools/list message"""
        message = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        response = await server._handle_message(message)
        
        assert response["id"] == 2
        assert "result" in response
        assert "tools" in response["result"]

    @pytest.mark.asyncio
    async def test_handle_message_call_tool(self, server):
        """Test handling a tools/call message"""
        message = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "simple",
                "arguments": {"text": "test"}
            }
        }
        
        response = await server._handle_message(message)
        
        assert response["id"] == 3
        assert "result" in response

    @pytest.mark.asyncio
    async def test_handle_message_invalid_method(self, server):
        """Test handling message with invalid method"""
        message = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "invalid_method",
            "params": {}
        }
        
        response = await server._handle_message(message)
        
        assert "error" in response
        assert response["error"]["code"] == -32601

    @pytest.mark.asyncio
    async def test_handle_message_notification(self, server):
        """Test handling a notification (no id)"""
        message = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {}
        }
        
        response = await server._handle_message(message)
        
        # Notifications don't get responses
        assert response is None

    @pytest.mark.asyncio
    async def test_error_response_format(self, server):
        """Test error response formatting"""
        error = server._error_response(1, -32600, "Invalid Request")
        
        assert error["jsonrpc"] == "2.0"
        assert error["id"] == 1
        assert "error" in error
        assert error["error"]["code"] == -32600
        assert error["error"]["message"] == "Invalid Request"

    @pytest.mark.asyncio
    async def test_run_method(self, mock_transport, server):
        """Test the run method (main server loop)"""
        # Make run_message_loop exit immediately
        mock_transport.run_message_loop = AsyncMock()
        
        await server.run()
        
        # Verify transport was started and stopped
        mock_transport.start.assert_called_once()
        mock_transport.stop.assert_called_once()
