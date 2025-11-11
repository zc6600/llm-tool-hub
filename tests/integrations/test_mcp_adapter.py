# tests/integrations/test_mcp_adapter.py

import pytest
from unittest.mock import Mock
from llm_tool_hub.integrations.mcp_adapter import MCPAdapter
from llm_tool_hub.base_tool import BaseTool


class DummyTool(BaseTool):
    """Test tool for MCP adapter testing"""
    name = "dummy_tool"
    description = "A dummy tool for testing"
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "limit": {"type": "integer", "description": "Result limit"},
        },
        "required": ["query"],
    }

    def run(self, query: str, limit: int = 5) -> str:
        return f"Results for '{query}' (limit: {limit})"


class ErrorTool(BaseTool):
    """Test tool that raises errors"""
    name = "error_tool"
    description = "A tool that raises errors"
    parameters = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    def run(self) -> str:
        raise RuntimeError("Test error")


class TestMCPAdapter:
    """Test suite for MCPAdapter"""

    @pytest.fixture
    def adapter(self):
        """Create adapter with test tools"""
        return MCPAdapter([DummyTool(), ErrorTool()])

    def test_adapter_initialization(self, adapter):
        """Test that adapter initializes with correct tools"""
        assert adapter.get_tool("dummy_tool") is not None
        assert adapter.get_tool("error_tool") is not None
        assert len(adapter.get_tools()) == 2

    def test_get_tool(self, adapter):
        """Test retrieving a tool by name"""
        tool = adapter.get_tool("dummy_tool")
        assert tool is not None
        assert tool.name == "dummy_tool"

    def test_get_nonexistent_tool(self, adapter):
        """Test getting a tool that doesn't exist"""
        tool = adapter.get_tool("nonexistent_tool")
        assert tool is None

    def test_list_tools(self, adapter):
        """Test listing tools in MCP format"""
        tools = adapter.list_tools()
        
        assert len(tools) == 2
        
        # Check dummy_tool
        dummy = next(t for t in tools if t["name"] == "dummy_tool")
        assert dummy["description"] == "A dummy tool for testing"
        assert "inputSchema" in dummy
        assert "properties" in dummy["inputSchema"]
        assert "required" in dummy["inputSchema"]

    def test_tool_to_mcp_schema(self, adapter):
        """Test converting a single tool to MCP schema"""
        tool = DummyTool()
        schema = adapter._tool_to_mcp_schema(tool)
        
        assert schema["name"] == "dummy_tool"
        assert schema["description"] == "A dummy tool for testing"
        assert "inputSchema" in schema
        assert schema["inputSchema"]["type"] == "object"
        assert "query" in schema["inputSchema"]["properties"]

    @pytest.mark.asyncio
    async def test_execute_tool_success(self, adapter):
        """Test executing a tool successfully"""
        result = await adapter.execute_tool("dummy_tool", {"query": "test"})
        
        assert "test" in result
        assert "Results for" in result

    @pytest.mark.asyncio
    async def test_execute_tool_with_all_args(self, adapter):
        """Test executing tool with all arguments"""
        result = await adapter.execute_tool(
            "dummy_tool",
            {"query": "test", "limit": 10}
        )
        
        assert "test" in result
        assert "10" in result

    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool(self, adapter):
        """Test executing a tool that doesn't exist"""
        with pytest.raises(ValueError, match="not found"):
            await adapter.execute_tool("nonexistent", {})

    @pytest.mark.asyncio
    async def test_execute_tool_with_invalid_args(self, adapter):
        """Test executing tool with missing required arguments"""
        with pytest.raises(ValueError, match="Invalid arguments"):
            await adapter.execute_tool("dummy_tool", {})  # missing required 'query'

    @pytest.mark.asyncio
    async def test_execute_tool_error_handling(self, adapter):
        """Test error handling during tool execution"""
        with pytest.raises(RuntimeError):
            await adapter.execute_tool("error_tool", {})

    def test_validate_arguments_success(self, adapter):
        """Test argument validation with valid arguments"""
        is_valid = adapter.validate_arguments("dummy_tool", {"query": "test"})
        assert is_valid is True

    def test_validate_arguments_missing_required(self, adapter):
        """Test argument validation with missing required parameter"""
        is_valid = adapter.validate_arguments("dummy_tool", {})
        assert is_valid is False

    def test_validate_arguments_nonexistent_tool(self, adapter):
        """Test argument validation for nonexistent tool"""
        is_valid = adapter.validate_arguments("nonexistent", {})
        assert is_valid is False
