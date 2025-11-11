# tests/integrations/test_function_adapter.py

"""
Unit tests for FunctionAdapter.

Tests the conversion of BaseTool instances to raw Python functions
and their various usage patterns.
"""

import pytest
from typing import Dict, Any
from unittest.mock import Mock, patch

from llm_tool_hub.base_tool import BaseTool
from llm_tool_hub.integrations.function_adapter import FunctionAdapter


class DummyTool(BaseTool):
    """A dummy tool for testing."""
    name: str = "dummy_tool"
    description: str = "A dummy tool for testing"
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "input": {"type": "string", "description": "Input text"}
        },
        "required": ["input"]
    }

    def run(self, input: str) -> str:
        return f"Processed: {input}"


class AnotherTool(BaseTool):
    """Another dummy tool for testing."""
    name: str = "another_tool"
    description: str = "Another tool for testing"
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "value": {"type": "integer", "description": "A number"}
        }
    }

    def run(self, value: int = 0) -> str:
        return f"Result: {value * 2}"


class TestFunctionAdapter:
    """Test suite for FunctionAdapter."""

    @pytest.fixture
    def tools(self):
        """Create test tools."""
        return [DummyTool(), AnotherTool()]

    @pytest.fixture
    def adapter(self, tools):
        """Create a FunctionAdapter instance."""
        return FunctionAdapter(tools)

    def test_adapter_initialization(self, adapter):
        """Test adapter initialization."""
        assert adapter is not None
        assert len(adapter) == 2
        assert "dummy_tool" in adapter
        assert "another_tool" in adapter

    def test_get_function_basic(self, adapter):
        """Test getting a function by name."""
        func = adapter.get_function("dummy_tool")
        assert func is not None
        assert callable(func)
        assert func.__name__ == "dummy_tool"

    def test_get_function_not_found(self, adapter):
        """Test getting a non-existent function."""
        func = adapter.get_function("nonexistent")
        assert func is None

    def test_function_execution(self, adapter):
        """Test executing a function."""
        func = adapter.get_function("dummy_tool")
        result = func(input="test")
        assert result == "Processed: test"

    def test_function_with_default_args(self, adapter):
        """Test executing a function with default arguments."""
        func = adapter.get_function("another_tool")
        result = func(value=5)
        assert result == "Result: 10"

    def test_function_with_no_args(self, adapter):
        """Test executing a function with no arguments."""
        func = adapter.get_function("another_tool")
        result = func()
        assert result == "Result: 0"

    def test_get_all_functions(self, adapter):
        """Test getting all functions."""
        functions = adapter.get_all_functions()
        assert len(functions) == 2
        assert all(callable(f) for f in functions)

    def test_get_functions_dict(self, adapter):
        """Test getting functions as dictionary."""
        funcs_dict = adapter.get_functions_dict()
        assert isinstance(funcs_dict, dict)
        assert len(funcs_dict) == 2
        assert "dummy_tool" in funcs_dict
        assert "another_tool" in funcs_dict
        assert callable(funcs_dict["dummy_tool"])

    def test_call_function_success(self, adapter):
        """Test calling a function through adapter."""
        result = adapter.call_function("dummy_tool", input="hello")
        assert result == "Processed: hello"

    def test_call_function_not_found(self, adapter):
        """Test calling a non-existent function raises error."""
        with pytest.raises(ValueError):
            adapter.call_function("nonexistent")

    def test_get_function_info_basic(self, adapter):
        """Test getting function information."""
        info = adapter.get_function_info("dummy_tool")
        assert info is not None
        assert info['name'] == "dummy_tool"
        assert "test" in info['description'].lower()
        assert 'parameters' in info
        assert 'parameters_json' in info

    def test_get_function_info_parameters(self, adapter):
        """Test function info includes parameter details."""
        info = adapter.get_function_info("dummy_tool")
        params_json = info['parameters_json']
        assert params_json['type'] == 'object'
        assert 'properties' in params_json
        assert 'input' in params_json['properties']
        assert 'required' in params_json

    def test_get_function_info_not_found(self, adapter):
        """Test getting info for non-existent function."""
        info = adapter.get_function_info("nonexistent")
        assert info is None

    def test_get_all_function_info(self, adapter):
        """Test getting information for all functions."""
        all_info = adapter.get_all_function_info()
        assert len(all_info) == 2
        assert "dummy_tool" in all_info
        assert "another_tool" in all_info
        assert all_info["dummy_tool"]['name'] == "dummy_tool"

    def test_dictionary_style_access(self, adapter):
        """Test accessing functions using dictionary syntax."""
        func = adapter["dummy_tool"]
        assert callable(func)
        result = func(input="test")
        assert result == "Processed: test"

    def test_dictionary_style_access_not_found(self, adapter):
        """Test dictionary access for non-existent tool."""
        with pytest.raises(KeyError):
            _ = adapter["nonexistent"]

    def test_empty_tools_list_raises_error(self):
        """Test that empty tools list raises ValueError."""
        with pytest.raises(ValueError):
            FunctionAdapter([])

    def test_invalid_tools_raises_error(self):
        """Test that invalid tools raise ValueError."""
        with pytest.raises(ValueError):
            FunctionAdapter(["not a tool"])

    def test_contains_operator(self, adapter):
        """Test the 'in' operator."""
        assert "dummy_tool" in adapter
        assert "another_tool" in adapter
        assert "nonexistent" not in adapter

    def test_len_operator(self, adapter):
        """Test the len() operator."""
        assert len(adapter) == 2

    def test_repr(self, adapter):
        """Test the string representation."""
        repr_str = repr(adapter)
        assert "FunctionAdapter" in repr_str
        assert "2 tools" in repr_str

    def test_function_metadata(self, adapter):
        """Test that functions have metadata attributes."""
        func = adapter.get_function("dummy_tool")
        assert hasattr(func, '__name__')
        assert hasattr(func, '__doc__')
        assert hasattr(func, 'json_schema')
        assert func.__name__ == "dummy_tool"
        assert func.__doc__ == "A dummy tool for testing"

    def test_call_function_with_error(self, adapter):
        """Test calling a function that raises an error."""
        # Create a tool that raises an error
        class ErrorTool(BaseTool):
            name: str = "error_tool"
            description: str = "Tool that raises error"
            parameters: Dict[str, Any] = {"type": "object", "properties": {}}

            def run(self) -> str:
                raise RuntimeError("Test error")

        adapter_with_error = FunctionAdapter([ErrorTool()])
        
        with pytest.raises(RuntimeError):
            adapter_with_error.call_function("error_tool")

    def test_multiple_function_calls(self, adapter):
        """Test calling multiple functions in sequence."""
        result1 = adapter.call_function("dummy_tool", input="first")
        result2 = adapter.call_function("another_tool", value=3)
        result3 = adapter.call_function("dummy_tool", input="second")

        assert result1 == "Processed: first"
        assert result2 == "Result: 6"
        assert result3 == "Processed: second"

    def test_function_isolation(self, tools):
        """Test that functions from different adapters are isolated."""
        adapter1 = FunctionAdapter([tools[0]])
        adapter2 = FunctionAdapter([tools[1]])

        assert len(adapter1) == 1
        assert len(adapter2) == 1
        assert adapter1["dummy_tool"] is not None
        assert adapter2["another_tool"] is not None
        # Each adapter should only have its own tool
        with pytest.raises(KeyError):
            _ = adapter1["another_tool"]
        with pytest.raises(KeyError):
            _ = adapter2["dummy_tool"]

    def test_get_all_function_info_with_multiple_tools(self, adapter):
        """Test getting complete information about all tools."""
        all_info = adapter.get_all_function_info()
        
        # Check dummy tool
        dummy_info = all_info["dummy_tool"]
        assert dummy_info['name'] == "dummy_tool"
        assert "input" in dummy_info['parameters_json']['properties']
        assert "input" in dummy_info['parameters_json']['required']

        # Check another tool
        another_info = all_info["another_tool"]
        assert another_info['name'] == "another_tool"
        assert "value" in another_info['parameters_json']['properties']
