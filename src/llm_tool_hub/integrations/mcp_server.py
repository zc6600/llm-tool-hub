# src/llm_tool_hub/integrations/mcp_server.py

import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional

from .mcp_adapter import MCPAdapter
from ..base_tool import BaseTool
from ..transports.base_transport import BaseTransport

logger = logging.getLogger(__name__)


class ToolHubMCPServer:
    """
    MCP (Model Context Protocol) Server implementation for llm-tool-hub.
    
    Exposes BaseTool instances as MCP-compatible tools that can be called
    by LLM clients (Claude, VS Code, etc.) via JSON-RPC protocol.
    
    The server handles:
    - Tool listing (tools/list)
    - Tool execution (tools/call)
    - Error handling and response formatting
    - Message routing and protocol compliance
    """

    def __init__(
        self,
        tools: List[BaseTool],
        transport: BaseTransport,
        server_name: str = "llm-tool-hub",
        server_version: str = "1.0.0",
    ):
        """
        Initialize the MCP server.
        
        Args:
            tools: List of BaseTool instances to expose
            transport: BaseTransport instance for communication
            server_name: Name of the server (for protocol)
            server_version: Version of the server
        """
        self.adapter = MCPAdapter(tools)
        self.transport = transport
        self.server_name = server_name
        self.server_version = server_version
        self._request_handlers: Dict[str, Callable] = {
            "initialize": self._handle_initialize,
            "tools/list": self._handle_list_tools,
            "tools/call": self._handle_call_tool,
        }
        logger.info(
            f"ToolHubMCPServer initialized with {len(tools)} tools: "
            f"{[tool.name for tool in tools]}"
        )

    async def run(self) -> None:
        """
        Start the MCP server and run the message loop.
        
        This is the main entry point - call this to start the server.
        """
        try:
            logger.info(f"Starting {self.server_name} MCP server")
            await self.transport.start()
            await self.transport.run_message_loop(self._handle_message)
        except KeyboardInterrupt:
            logger.info("Server interrupted by user")
        except Exception as e:
            logger.error(f"Server error: {e}", exc_info=True)
        finally:
            await self.transport.stop()
            logger.info("Server stopped")

    async def _handle_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Handle an incoming JSON-RPC message.
        
        Args:
            message: The incoming JSON-RPC request/notification
            
        Returns:
            Response dict to send back, or None for notifications
        """
        try:
            # Validate JSON-RPC 2.0 format
            if not isinstance(message, dict):
                return self._error_response(None, -32700, "Parse error")
            
            method = message.get("method")
            params = message.get("params", {})
            msg_id = message.get("id")
            
            if not method:
                return self._error_response(msg_id, -32600, "Invalid Request")
            
            logger.debug(f"Handling request: method={method}, id={msg_id}")
            
            # Route to appropriate handler
            handler = self._request_handlers.get(method)
            if not handler:
                return self._error_response(msg_id, -32601, f"Method not found: {method}")
            
            # Call the handler
            result = await handler(params)
            
            # Format response (only if it's a request with id, not a notification)
            if msg_id is not None:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": result,
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            msg_id = message.get("id") if isinstance(message, dict) else None
            return self._error_response(msg_id, -32603, f"Internal error: {str(e)}")

    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the initialize request.
        
        This is the first request sent by the client.
        
        Args:
            params: Initialize parameters
            
        Returns:
            Server capabilities and info
        """
        logger.info(f"Client initializing: {params.get('clientInfo', {}).get('name', 'unknown')}")
        
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": self.server_name,
                "version": self.server_version,
            },
        }

    async def _handle_list_tools(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the tools/list request.
        
        Returns available tools to the client.
        
        Args:
            params: List parameters (usually empty)
            
        Returns:
            Dict with tools list
        """
        tools = self.adapter.list_tools()
        logger.debug(f"Listing {len(tools)} tools")
        
        return {
            "tools": tools
        }

    async def _handle_call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the tools/call request.
        
        Executes a tool and returns the result.
        
        Args:
            params: Dict with 'name' (tool name) and 'arguments' (tool arguments)
            
        Returns:
            Tool execution result
            
        Raises:
            ValueError: If tool name is missing or tool not found
        """
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not tool_name:
            raise ValueError("Tool name is required")
        
        logger.info(f"Calling tool: {tool_name} with args: {arguments}")
        
        try:
            # Execute the tool through the adapter
            result = await self.adapter.execute_tool(tool_name, arguments)
            
            logger.debug(f"Tool {tool_name} executed successfully")
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": result
                    }
                ]
            }
            
        except ValueError as e:
            logger.error(f"Invalid arguments for tool {tool_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Tool execution failed: {e}", exc_info=True)
            raise

    def _error_response(
        self,
        msg_id: Optional[Any],
        code: int,
        message: str,
        data: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Create a JSON-RPC error response.
        
        Args:
            msg_id: The request ID (or None for notifications)
            code: JSON-RPC error code
            message: Error message
            data: Optional additional error data
            
        Returns:
            Error response dict
        """
        error: Dict[str, Any] = {
            "code": code,
            "message": message,
        }
        
        if data is not None:
            error["data"] = data
        
        response: Dict[str, Any] = {
            "jsonrpc": "2.0",
            "error": error,
        }
        
        if msg_id is not None:
            response["id"] = msg_id
        
        return response
