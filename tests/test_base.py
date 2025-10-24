# tests/test_base.py

import pytest
from llm_tool_hub.base_tool import BaseTool
from typing import Dict, Any

# -----------------------------------
# Helper Mock Class for Testing the BaseTool Contract
# -----------------------------------

# 1. Define a concrete class that correctly implements the constract
class CorrectlyImplementedTool(BaseTool):
    name: str = "mock_tool"
    description: str = "A mock tool for testing purpose."
    parameters: Dict[str, Any] = {"type": "object", "properties": {}}

    def run(self, **kwargs) -> str:
        return "Executed successfully"
    
# -----------------------------------
# Tests
# -----------------------------------

def test_base_tool_instantiation_success():
    try:
        tool = CorrectlyImplementedTool()
        assert tool.name == "mock_tool"
    except NotImplementedError:
        pytest.fail("Correctly implemented tool raised NotImplementedError unexpectedly")

def test_base_tool_enforces_metadata():
    class MissingNameTool(BaseTool):
        description: str = "Missing name."
        parameters: Dict[str, Any] = {"type": "object", "properties": {}}

        def run(self, **kwargs)-> str:
            return ""
        
    with pytest.raises(NotImplementedError) as excinfo:
        MissingNameTool()
    assert "must define 'name'" in str(excinfo.value)