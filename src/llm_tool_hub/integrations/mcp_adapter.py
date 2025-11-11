# src/llm_tool_hub/integrations/mcp_adapter.py

import logging
from typing import Any, Dict, List, Optional
from ..base_tool import BaseTool

logger = logging.getLogger(__name__)


class MCPAdapter:
    """
    Adapter to convert llm-tool-hub BaseTool instances to MCP-compatible format.
    
    Handles:
    - Tool definition conversion to MCP schema
    - Tool execution with argument mapping
    - Error handling and response formatting
    """

    def __init__(self, tools: List[BaseTool]):
        """
        Initialize the MCP adapter with a list of tools.
        
        Args:
            tools: List of BaseTool instances to expose via MCP
        """
        self.tools: Dict[str, BaseTool] = {tool.name: tool for tool in tools}
        logger.info(f"MCPAdapter initialized with {len(self.tools)} tools: {list(self.tools.keys())}")

    def get_tools(self) -> List[BaseTool]:
        """
        Get all registered tools.
        
        Returns:
            List of BaseTool instances
        """
        return list(self.tools.values())

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        Get a specific tool by name.
        
        Args:
            name: Name of the tool
            
        Returns:
            BaseTool instance or None if not found
        """
        return self.tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        Get MCP-compatible tool definitions.
        
        Returns:
            List of tool definitions in MCP format
        """
        return [self._tool_to_mcp_schema(tool) for tool in self.tools.values()]

    def _tool_to_mcp_schema(self, tool: BaseTool) -> Dict[str, Any]:
        """
        Convert a BaseTool to MCP tool schema format.
        
        Args:
            tool: BaseTool instance to convert
            
        Returns:
            MCP tool schema dict with name, description, and inputSchema
        """
        return {
            "name": tool.name,
            "description": tool.description,
            "inputSchema": {
                "type": "object",
                "properties": tool.parameters.get("properties", {}),
                "required": tool.parameters.get("required", []),
            },
        }

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> str:
        """
        Execute a tool with the given arguments.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Arguments to pass to the tool
            
        Returns:
            Tool execution result as a string
            
        Raises:
            ValueError: If tool not found
            Exception: If tool execution fails
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found. Available tools: {list(self.tools.keys())}")
        
        tool = self.tools[tool_name]
        
        try:
            logger.info(f"Executing tool '{tool_name}' with arguments: {arguments}")
            # Execute the tool synchronously (tools use run() not async)
            result = tool.run(**arguments)
            logger.info(f"Tool '{tool_name}' executed successfully")
            return str(result)
        except TypeError as e:
            # Handle invalid arguments
            raise ValueError(f"Invalid arguments for tool '{tool_name}': {e}")
        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}': {e}", exc_info=True)
            raise

    def validate_arguments(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> bool:
        """
        Validate arguments against a tool's schema.
        
        Args:
            tool_name: Name of the tool
            arguments: Arguments to validate
            
        Returns:
            True if arguments are valid, False otherwise
        """
        if tool_name not in self.tools:
            return False
        
        tool = self.tools[tool_name]
        required_params = tool.parameters.get("required", [])
        
        # Check all required parameters are present
        for param in required_params:
            if param not in arguments:
                return False
        
        return True
