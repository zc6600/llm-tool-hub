# src/llm_tool_hub/integrations/langchain_adapter.py

import logging
from typing import Type, Any, Dict, Union
from pydantic import BaseModel, create_model

from ..base_tool import BaseTool # Relative import to BaseTool

logger = logging.getLogger(__name__)

# Define Pydantic base types for JSON Schema mapping
PYDANTIC_TYPE_MAP = {
    "string": str,
    "number": float,
    "integer": int,
    "boolean": bool
}

class LangchainToolAdapter:
    """
    Provides methods to adapt llm-tool-hub's BaseTool subclasses into native 
    LangChain structures (specifically StructuredTool).
    
    This is the dedicated integration point for LangChain developers.
    """
    
    @staticmethod
    def _create_pydantic_schema(tool_instance: BaseTool) -> Type[BaseModel]:
        """
        Converts the BaseTool's JSON Schema 'parameters' into a Pydantic Model, 
        which is required by LangChain's StructuredTool.
        """
        json_properties = tool_instance.parameters.get("properties", {})
        json_required = tool_instance.parameters.get("required", [])
        
        pydantic_fields = {}

        for name, prop in json_properties.items():
            json_type = prop.get("type", "string")
            py_type = PYDANTIC_TYPE_MAP.get(json_type, str)
            
            # Determine if the field is required or optional (Union[Type, None])
            is_required = name in json_required
            
            # Pydantic field definition (Type, Default/Ellipsis)
            if is_required:
                field_info = (py_type, ...) # Ellipsis means required
            else:
                field_info = (Union[py_type, None], None) # Optional, default to None
            
            pydantic_fields[name] = field_info

        # Dynamically create the Pydantic input model
        # Name convention: ToolNameInput (e.g., ShellToolInput)
        InputSchema = create_model(
            f"{tool_instance.name.capitalize()}Input", 
            __base__=BaseModel,
            **pydantic_fields
        )
        
        return InputSchema

    @staticmethod
    def to_langchain_structured_tool(tool_instance: BaseTool) -> Any:
        """
        Converts a BaseTool instance into a LangChain StructuredTool instance.

        :param tool_instance: An initialized instance of a BaseTool subclass.
        :return: A LangChain StructuredTool instance.
        :raises ImportError: If LangChain core components are not installed.
        """
        try:
            # We specifically target langchain_core for stability
            from langchain_core.tools import StructuredTool
        except ImportError:
            raise ImportError(
                "LangChain core components are not installed. Please install them "
                "to use the LangchainToolAdapter (e.g., `pip install langchain-core`)."
            )

        # 1. Create the Pydantic Input Schema
        InputSchema = LangchainToolAdapter._create_pydantic_schema(tool_instance)

        # 2. Create the StructuredTool
        # StructuredTool.from_function handles the automatic argument passing
        # from the Pydantic model to the function (tool_instance.run).
        lc_tool = StructuredTool.from_function(
            func=tool_instance.run,
            name=tool_instance.name,
            description=tool_instance.description,
            args_schema=InputSchema
        )

        return lc_tool