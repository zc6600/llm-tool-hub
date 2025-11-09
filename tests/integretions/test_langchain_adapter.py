# tests/integrations/test_tool_registry.py

import pytest
import json
from pathlib import Path
from typing import Dict, Any, Union

from llm_tool_hub.integrations.tool_registry import ToolRegistry
from llm_tool_hub.base_tool import BaseTool
from llm_tool_hub.shell_tool.shell_tool import ShellTool

# --- Mock Tools for Testing ---

class MockCalculatorTool(BaseTool):
    """A mock tool to test successful execution and argument passing."""
    name: str = "mock_calculator"
    description: str = "A tool to perform basic addition."
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "a": {"type": "number", "description": "The first number."},
            "b": {"type": "number", "description": "The second number."},
            "op": {"type": "string", "description": "Operation type.", "enum": ["add", "sub"], "default": "add"},
        },
        "required": ["a", "b"]
    }

    def run(self, a: float, b: float, op: str = "add") -> str:
        if op == "add":
            return f"Result: {a + b}"
        elif op == "sub":
            return f"Result: {a - b}"
        return "Invalid operation"

class MockErrorTool(BaseTool):
    """A mock tool that always raises an error."""
    name: str = "mock_error"
    description: str = "A tool that simulates an internal error."
    parameters: Dict[str, Any] = {"type": "object", "properties": {}}

    def run(self) -> str:
        raise ValueError("Simulated internal tool error.")

# --- Fixtures ---

@pytest.fixture
def test_registry(tmp_path: Path) -> ToolRegistry:
    """Fixture to create a registry with various tools."""
    tools = [
        ShellTool(root_path=tmp_path),
        MockCalculatorTool(),
        MockErrorTool()
    ]
    return ToolRegistry(tools=tools)

# ==============================================================================
# A. Initialization and Discovery Tests
# ==============================================================================

def test_registry_initialization_success(test_registry: ToolRegistry):
    """A.1: Tests successful initialization and correct storage of tools."""
    assert len(test_registry.tools) == 3
    assert isinstance(test_registry.tools["shell_tool"], ShellTool)
    assert isinstance(test_registry.tools["mock_calculator"], MockCalculatorTool)

def test_registry_initialization_duplicate_names(tmp_path: Path):
    """A.2: Ensures duplicate tool names are handled (the duplicate is ignored with a warning)."""
    tool1 = MockCalculatorTool()
    tool2 = MockCalculatorTool() # Same name: mock_calculator
    
    # ToolRegistry should only register one and ignore the second
    registry = ToolRegistry(tools=[tool1, tool2])
    assert len(registry.tools) == 1
    assert "mock_calculator" in registry.tools

# ==============================================================================
# B. Tool Description (JSON Schema) Tests
# ==============================================================================

def test_get_tool_descriptions_format(test_registry: ToolRegistry):
    """B.1: Verifies the output format conforms to the standard LLM JSON Schema."""
    descriptions = test_registry.get_tool_descriptions()
    
    assert len(descriptions) == 3
    
    calc_desc = next(d for d in descriptions if d['function']['name'] == 'mock_calculator')
    
    # Check top-level structure
    assert calc_desc['type'] == 'function'
    
    # Check function details
    func = calc_desc['function']
    assert func['name'] == 'mock_calculator'
    assert 'addition' in func['description'] # Check part of description
    
    # Check parameters structure
    params = func['parameters']
    assert params['type'] == 'object'
    assert 'a' in params['properties']
    assert 'b' in params['properties']
    assert 'required' in params
    assert 'a' in params['required'] # Check required fields

def test_get_tool_descriptions_empty_parameters(test_registry: ToolRegistry):
    """B.2: Verifies tools with empty/missing parameters are handled gracefully."""
    descriptions = test_registry.get_tool_descriptions()
    error_desc = next(d for d in descriptions if d['function']['name'] == 'mock_error')
    
    params = error_desc['function']['parameters']
    assert params['type'] == 'object'
    # The default fallback should result in no properties
    assert params['properties'] == {}

# ==============================================================================
# C. Execution Dispatch Tests
# ==============================================================================

def test_execute_tool_call_success(test_registry: ToolRegistry):
    """C.1: Tests successful execution of a tool with arguments."""
    # LLM calls: mock_calculator(a=10, b=5, op="sub")
    result = test_registry.execute_tool_call(
        tool_name="mock_calculator",
        a=10.0,
        b=5.0,
        op="sub"
    )
    assert result == "Result: 5.0"

def test_execute_tool_call_shell_tool_integration(test_registry: ToolRegistry):
    """C.2: Tests execution of ShellTool to verify structured output."""
    # LLM calls: shell_tool(command="echo hello")
    result_str = test_registry.execute_tool_call(
        tool_name="shell_tool",
        command="echo hello world"
    )
    # Check ShellTool's structured output format
    assert result_str.startswith("--- SHELL COMMAND RESULT ---")
    assert "STATUS: SUCCESS" in result_str
    assert "hello world" in result_str # Verify content

def test_execute_tool_call_internal_tool_error(test_registry: ToolRegistry):
    """C.3: Tests handling of internal errors raised by the tool's run method."""
    # LLM calls: mock_error()
    result = test_registry.execute_tool_call(tool_name="mock_error")
    
    # C.3 Fix: Assert it's an ERROR and contains the specific message
    assert result.startswith("ERROR:")
    assert "Simulated internal tool error" in result

def test_execute_tool_call_invalid_arguments_type_error(test_registry: ToolRegistry):
    """C.4: Tests handling when LLM provides insufficient arguments (causing TypeError)."""
    # LLM calls: mock_calculator(a=10) -- Missing required 'b'
    # The error should be caught as TypeError in run method
    result = test_registry.execute_tool_call(
        tool_name="mock_calculator",
        a=10.0
    )
    
    assert result.startswith("ERROR: Tool execution failed. Invalid arguments for 'mock_calculator'.")
    # C.4 Fix: Assert it's a missing positional argument error
    assert "missing 1 required positional argument" in result or "TypeError" in result
    
def test_execute_tool_call_non_existent_tool(test_registry: ToolRegistry):
    """C.5: Tests handling when LLM calls an unregistered tool."""
    # LLM calls: non_existent_tool()
    result = test_registry.execute_tool_call(tool_name="non_existent_tool")
    
    # C.5 Fix: Match the full string returned by the ToolRegistry's ValueError catch.
    assert result.startswith("ERROR: Tool execution failed. Reason:")
    assert "is not registered in the ToolRegistry" in result