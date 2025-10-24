# src/llm_tool_hub/base_tool.py


from abc import ABC, abstractmethod
from typing import Dict, Any, Callable
# ---------------------------
# 1. BaseTool Abstract Base Class
# ---------------------------
class BaseTool(ABC):
    """
    The Abstract Base Class(ABC) for all LLM-callable tools

    The class enforces a standardized API, requiring every concrete tool to 
    define the necessary metadata(name, description, parameters) 
    and implement the core excution logic (run).
    """
    # --- Class Attributes ---

    # Machine-readable tool name (str). Must be unique across all tools.
    name: str = ""

    # Detailed natural language description (str) used by the LLM to decide when and how to call the tool.
    description: str = ""

    # JSON Schema (Dict[str, Any]) defining the input arguments for the 'run' method.
    # Following the standard LLM Function Calling format
    # Example: {"type": "object". "properties": {...}, "required": ["..."]}
    parameters: Dict[str, Any] = {}

    # ------------------------------

    def __init__(self, **kwargs):
        """
        Initializes the base tool instance.

        Subclasses can pass custom configuration through kwargs.
        Checks for the presence of required metadata.  
        """

        if not self.name or not self.description:
            raise NotImplementedError(
                "Tool subclass must define 'name' and 'description' class attributes."
            )
        pass

    @abstractmethod
    def run(self, **kwargs) -> str:
        """
        Abstract method: Executes the tool's core functionality.
        """
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """
        Returns the tool's meta dictionary in the format required by 
        """
        return {
            "name": self.name, 
            "description": self.description,
            "parameters": self.parameters
        }
    
    def to_callable(self) -> Callable:
        """
        Returns a callable function object the wraps the 'run' method and
        dynamically attaches the tool's metadata.

        This facilitates easy integration with frameworks (like LangChain or LlamaIndex)
        that register tools using simple function objects.
         
        :return: A callable function with metadata attributes.
        """
        tool_function = self.run

        tool_function.__name__ = self.name
        tool_function.__doc__ = self.description
        setattr(tool_function, 'json_schema', self.parameters)

        return tool_function
    
    def __str__(self) -> str:
        """Provides a debugging-friendly string representation."""
        return f"<BaseTool: {self.name}>"
