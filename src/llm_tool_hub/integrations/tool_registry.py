# src/llm_tool_hub/integrations/tool_registry.py

import logging
from typing import List, Dict, Any, Type, Union
from ..base_tool import BaseTool # Relative import to BaseTool

logger = logging.getLogger(__name__)

class ToolRegistry:
    """
    A central registry for managing and adapting tools for generic LLM integration.

    This class serves as the primary integration gateway for developers using 
    native LLM APIs (like OpenAI, Gemini) and custom agent frameworks. 
    It converts BaseTool instances into standardized JSON Schema descriptions 
    and provides a unified execution interface.
    """

    def __init__(self, tools: List[BaseTool]):
        """
        Initializes the registry with a list of BaseTool instances provided by the developer.

        :param tools: A list of initialized BaseTool objects.
        :raises ValueError: If a tool is missing a 'name' attribute.
        """
        self.tools: Dict[str, BaseTool] = {}
        for tool in tools:
            if not tool.name:
                raise ValueError(f"Tool instance of type {type(tool).__name__} must define a 'name' attribute.")
            if tool.name in self.tools:
                logger.warning(f"Duplicate tool name registered: {tool.name}. Skipping the duplicate instance.")
                continue
            self.tools[tool.name] = tool
            logger.debug(f"Tool registered: {tool.name}")


    @staticmethod
    def _create_json_schema(tool_class: Type[BaseTool]) -> Dict[str, Any]:
        """
        [Internal Method] Converts BaseTool metadata into the LLM API compatible 
        JSON Schema format (OpenAI/Gemini function calling standard).

        :param tool_class: The subclass of BaseTool (e.g., ShellTool).
        :return: A standardized tool description dictionary.
        """
        
        # Ensure parameters definition is valid, falling back to empty if necessary
        params = tool_class.parameters
        if not params or params.get("type") != "object":
            logger.warning(
                f"Tool '{tool_class.name}' has invalid or missing 'parameters' definition. "
                "Defaulting to an empty parameters object."
            )
            params = {"type": "object", "properties": {}}
        
        # Construct the standard function calling format
        schema = {
            "type": "function",
            "function": {
                "name": tool_class.name,
                "description": tool_class.description,
                "parameters": params,
            }
        }
        return schema

    def get_tool_descriptions(self) -> List[Dict[str, Any]]:
        """
        Returns a list of standardized JSON Schema descriptions for all registered tools.
        This is the primary output consumed by LLM APIs during the request phase.
        """
        descriptions = []
        for tool in self.tools.values():
            descriptions.append(self._create_json_schema(type(tool)))
        return descriptions

    def get_tool_instance(self, name: str) -> BaseTool:
        """
        Retrieves an initialized tool instance by its registered name.

        :param name: The name of the tool to retrieve (e.g., 'shell_tool').
        :return: The BaseTool instance.
        :raises ValueError: If the tool is not registered.
        """
        if name not in self.tools:
            raise ValueError(f"Tool '{name}' is not registered in the ToolRegistry.")
        return self.tools[name]

    def execute_tool_call(self, tool_name: str, **kwargs) -> str:
        """
        A unified execution method called by the Agent framework after parsing 
        an LLM's tool call request.

        :param tool_name: The name of the tool requested by the LLM.
        :param kwargs: Arguments provided by the LLM for the tool's run method.
        :return: The string result from the tool's run method.
        """
        try:
            tool_instance = self.get_tool_instance(tool_name)
            
            logger.info(f"Executing tool: {tool_name} with args: {kwargs}")
            
            # Dispatch the call to the tool instance's run method
            result = tool_instance.run(**kwargs)
            
            logger.info(f"Tool {tool_name} executed successfully. Result length: {len(result)}")
            return result
        
        except ValueError as e:
            # Handles tool not found error from get_tool_instance
            return f"ERROR: Tool execution failed. Reason: {e}"
        except TypeError as e:
            # Handles argument mismatch error (LLM provided wrong args for run method)
            return f"ERROR: Tool execution failed. Invalid arguments for '{tool_name}'. Details: {e}"
        except Exception as e:
            # Catch all other unexpected runtime errors from the tool's run method
            logger.error(f"Unexpected runtime error during execution of {tool_name}: {e}")
            return f"FATAL ERROR: An unexpected error occurred during tool execution: {type(e).__name__}: {str(e)}"