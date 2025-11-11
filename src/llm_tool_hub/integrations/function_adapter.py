# src/llm_tool_hub/integrations/function_adapter.py

"""
Function Adapter for llm-tool-hub

This adapter converts BaseTool instances to raw Python functions.
It provides a simple way to use tools as regular Python callables,
without any framework-specific wrapping.

Usage:
    >>> from llm_tool_hub.filesystem_tool.read_file_tool import ReadFileTool
    >>> from llm_tool_hub.integrations.function_adapter import FunctionAdapter
    >>>
    >>> tool = ReadFileTool()
    >>> adapter = FunctionAdapter([tool])
    >>>
    >>> # Get the raw function
    >>> func = adapter.get_function("read_file")
    >>> result = func(file_path="/path/to/file.txt")
    >>>
    >>> # List all functions with their signatures
    >>> functions = adapter.get_all_functions()
    >>> for func in functions:
    ...     print(f"{func.__name__}: {func.__doc__}")
"""

import logging
from typing import Dict, List, Callable, Optional, Any
from ..base_tool import BaseTool

logger = logging.getLogger(__name__)


class FunctionAdapter:
    """
    Adapter for converting BaseTool instances to raw Python functions.
    
    This adapter provides direct access to tools as callable Python functions
    without any framework-specific wrapping (no LangChain, no MCP, just pure Python).
    
    Benefits:
    - Simple, Pythonic interface
    - No external dependencies
    - Easy integration with existing Python code
    - Functions retain metadata via attributes
    - Type hints preserved
    """

    def __init__(self, tools: List[BaseTool]):
        """
        Initialize the adapter with a list of tools.
        
        Args:
            tools: List of BaseTool instances to convert
            
        Raises:
            ValueError: If tools list is empty or contains invalid items
        """
        if not tools:
            raise ValueError("Tools list cannot be empty")
        
        if not all(isinstance(tool, BaseTool) for tool in tools):
            raise ValueError("All items must be BaseTool instances")
        
        self.tools: Dict[str, BaseTool] = {tool.name: tool for tool in tools}
        self.functions: Dict[str, Callable] = {
            tool.name: tool.to_callable() for tool in tools
        }
        
        logger.info(
            f"FunctionAdapter initialized with {len(self.tools)} tools: "
            f"{list(self.tools.keys())}"
        )

    def get_function(self, tool_name: str) -> Optional[Callable]:
        """
        Get a raw Python function for a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Callable function, or None if tool not found
            
        Example:
            >>> func = adapter.get_function("read_file")
            >>> result = func(file_path="/path/to/file.txt")
        """
        func = self.functions.get(tool_name)
        if not func:
            logger.warning(f"Tool '{tool_name}' not found in available functions")
            return None
        return func

    def get_all_functions(self) -> List[Callable]:
        """
        Get all tools as raw Python functions.
        
        Returns:
            List of callable functions
            
        Example:
            >>> functions = adapter.get_all_functions()
            >>> for func in functions:
            ...     print(f"{func.__name__}: {func.__doc__}")
        """
        return list(self.functions.values())

    def get_functions_dict(self) -> Dict[str, Callable]:
        """
        Get all tools as a dictionary mapping tool names to functions.
        
        Returns:
            Dictionary with tool names as keys and callables as values
            
        Example:
            >>> funcs_dict = adapter.get_functions_dict()
            >>> result = funcs_dict["shell_tool"](command="ls -la")
        """
        return dict(self.functions)

    def call_function(self, tool_name: str, **kwargs) -> str:
        """
        Call a tool function with keyword arguments.
        
        Args:
            tool_name: Name of the tool to call
            **kwargs: Arguments to pass to the tool function
            
        Returns:
            Result from the tool function (typically a string)
            
        Raises:
            ValueError: If tool not found
            Exception: Any exceptions raised by the tool function
            
        Example:
            >>> result = adapter.call_function("read_file", file_path="data.txt")
        """
        func = self.get_function(tool_name)
        if not func:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        try:
            result = func(**kwargs)
            return result
        except Exception as e:
            logger.error(f"Error calling '{tool_name}': {str(e)}")
            raise

    def get_function_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a tool's function.
        
        Returns function name, docstring, and parameter schema.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Dictionary with function info, or None if tool not found
            
        Example:
            >>> info = adapter.get_function_info("read_file")
            >>> print(info)
            {
                'name': 'read_file',
                'description': 'Read file contents...',
                'parameters': {...},
                'parameters_json': {...}
            }
        """
        tool = self.tools.get(tool_name)
        if not tool:
            return None
        
        return {
            'name': tool.name,
            'description': tool.description,
            'parameters': tool.parameters,
            'parameters_json': {
                'type': 'object',
                'properties': tool.parameters.get('properties', {}),
                'required': tool.parameters.get('required', [])
            }
        }

    def get_all_function_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all tools' functions.
        
        Returns:
            Dictionary mapping tool names to their info
            
        Example:
            >>> all_info = adapter.get_all_function_info()
            >>> for name, info in all_info.items():
            ...     print(f"{name}: {info['description']}")
        """
        return {
            name: self.get_function_info(name)
            for name in self.tools.keys()
        }

    def __len__(self) -> int:
        """Return the number of available functions."""
        return len(self.functions)

    def __contains__(self, tool_name: str) -> bool:
        """Check if a tool is available."""
        return tool_name in self.tools

    def __getitem__(self, tool_name: str) -> Callable:
        """
        Get a function using dictionary-style access.
        
        Example:
            >>> read_func = adapter["read_file"]
            >>> result = read_func(file_path="data.txt")
        """
        func = self.get_function(tool_name)
        if not func:
            raise KeyError(f"Tool '{tool_name}' not found")
        return func

    def __repr__(self) -> str:
        """Return a string representation of the adapter."""
        tool_names = ", ".join(self.tools.keys())
        return f"FunctionAdapter({len(self.tools)} tools: [{tool_names}])"
