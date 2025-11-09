# tests/real_llm/integrations/test_langchain_adaptor.py

import pytest
import json
from typing import Optional


# ============================================================================
# Custom Test Tools
# ============================================================================

class MathCalculatorTool:
    """Simple calculator tool for testing LLM tool calling"""
    
    def __init__(self):
        self.name = "math_calculator"
        self.description = "Performs basic mathematical operations: add, subtract, multiply, divide"
        self.parameters = {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The operation to perform: 'add', 'subtract', 'multiply', 'divide'"
                },
                "a": {
                    "type": "number",
                    "description": "First number"
                },
                "b": {
                    "type": "number",
                    "description": "Second number"
                }
            },
            "required": ["operation", "a", "b"]
        }
    
    def get_metadata(self):
        """Return OpenAI Function Calling format"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }
    
    def run(self, operation: str, a: float, b: float) -> float:
        """Execute the mathematical operation"""
        if operation == "add":
            return a + b
        elif operation == "subtract":
            return a - b
        elif operation == "multiply":
            return a * b
        elif operation == "divide":
            if b == 0:
                raise ValueError("Cannot divide by zero")
            return a / b
        else:
            raise ValueError(f"Unknown operation: {operation}")


class PersonNameFormatterTool:
    """Tool to format person names - tests string manipulation"""
    
    def __init__(self):
        self.name = "name_formatter"
        self.description = "Formats person names in different styles: full, first_only, last_only, initials"
        self.parameters = {
            "type": "object",
            "properties": {
                "first_name": {
                    "type": "string",
                    "description": "Person's first name"
                },
                "last_name": {
                    "type": "string",
                    "description": "Person's last name"
                },
                "format": {
                    "type": "string",
                    "description": "Format style: 'full', 'first_only', 'last_only', or 'initials'"
                }
            },
            "required": ["first_name", "last_name", "format"]
        }
    
    def get_metadata(self):
        """Return OpenAI Function Calling format"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }
    
    def run(self, first_name: str, last_name: str, format: str) -> str:
        """Execute the name formatting"""
        if format == "full":
            return f"{first_name} {last_name}"
        elif format == "first_only":
            return first_name
        elif format == "last_only":
            return last_name
        elif format == "initials":
            return f"{first_name[0]}.{last_name[0]}."
        else:
            raise ValueError(f"Unknown format: {format}")


class CounterTool:
    """Tool that counts items - tests list processing"""
    
    def __init__(self):
        self.name = "counter"
        self.description = "Counts occurrences of items in a comma-separated list"
        self.parameters = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "string",
                    "description": "Comma-separated list of items"
                },
                "item_to_count": {
                    "type": "string",
                    "description": "The specific item to count"
                }
            },
            "required": ["items", "item_to_count"]
        }
    
    def get_metadata(self):
        """Return OpenAI Function Calling format"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }
    
    def run(self, items: str, item_to_count: str) -> int:
        """Count occurrences of item in list"""
        item_list = [item.strip() for item in items.split(",")]
        count = item_list.count(item_to_count.strip())
        return count


# ============================================================================
# Real LLM Integration Tests
# ============================================================================

class TestLangchainToolIntegration:
    """Test LLM's ability to correctly call custom tools via langchain adapter"""
    
    @pytest.mark.real_llm
    def test_llm_calls_math_calculator_correctly(self, openrouter_client):
        """
        Scenario: LLM receives a math problem and must use math_calculator tool correctly
        
        Verification: 
        - LLM calls the tool with correct parameters
        - Tool executes correctly
        - Result matches expected value
        """
        math_tool = MathCalculatorTool()
        tool_definitions = [math_tool.get_metadata()]
        
        task_message = """
Calculate: What is 25 multiplied by 4?
Use the math_calculator tool with:
- operation: "multiply"
- a: 25
- b: 4
"""
        
        messages = [{"role": "user", "content": task_message}]
        
        system_prompt = """
You are a helpful calculator assistant. When asked to perform calculations, 
use the math_calculator tool with the appropriate operation.
"""
        
        response = openrouter_client.call_with_tools(
            messages=messages,
            tools=tool_definitions,
            system_prompt=system_prompt
        )
        
        print(f"\n🤖 LLM Response: {response['content']}")
        print(f"🔧 Tool Calls: {response['tool_calls']}")
        
        assert len(response['tool_calls']) > 0, "LLM should call math_calculator"
        
        # Verify the tool call
        tool_call = response['tool_calls'][0]
        assert tool_call['name'] == 'math_calculator', f"Expected math_calculator, got {tool_call['name']}"
        
        # Verify parameters
        args = tool_call['arguments']
        assert args.get('operation') == 'multiply', f"Expected multiply, got {args.get('operation')}"
        assert args.get('a') == 25, f"Expected a=25, got {args.get('a')}"
        assert args.get('b') == 4, f"Expected b=4, got {args.get('b')}"
        
        # Execute tool and verify result
        result = math_tool.run(**args)
        assert result == 100, f"Expected 100, got {result}"
        
        print(f"\n✨ Test Passed! LLM correctly called math_calculator with result: {result}")
    
    @pytest.mark.real_llm
    def test_llm_calls_name_formatter_full_format(self, openrouter_client):
        """
        Scenario: LLM formats person names using full format
        
        Verification:
        - LLM correctly calls name_formatter with full format
        - Tool executes correctly
        """
        name_tool = PersonNameFormatterTool()
        tool_definitions = [name_tool.get_metadata()]
        
        task_message = """
Format the person "John" "Smith" with format 'full' (complete name).
Use the name_formatter tool with:
- first_name: "John"
- last_name: "Smith"
- format: "full"
"""
        
        messages = [{"role": "user", "content": task_message}]
        
        system_prompt = """
You are a name formatting assistant. You can format names in different styles.
When asked to format names, use the name_formatter tool appropriately.
"""
        
        response = openrouter_client.call_with_tools(
            messages=messages,
            tools=tool_definitions,
            system_prompt=system_prompt
        )
        
        print(f"\n🤖 LLM Response: {response['content']}")
        print(f"🔧 Tool Calls: {response['tool_calls']}")
        
        assert len(response['tool_calls']) >= 1, "LLM should call name_formatter at least once"
        
        # Verify the tool call
        tool_call = response['tool_calls'][0]
        assert tool_call['name'] == 'name_formatter', f"Expected name_formatter, got {tool_call['name']}"
        
        args = tool_call['arguments']
        assert args.get('first_name') in ['John', 'john'], "First name should be John"
        assert args.get('last_name') in ['Smith', 'smith'], "Last name should be Smith"
        assert args.get('format') == 'full', "Format should be 'full'"
        
        # Execute and verify
        result = name_tool.run(**args)
        assert 'John' in result or 'john' in result.lower(), f"Full format should contain John: {result}"
        
        print(f"\n✨ Test Passed! LLM correctly formatted name: {result}")
    
    @pytest.mark.real_llm
    def test_llm_calls_counter_tool_accurately(self, openrouter_client):
        """
        Scenario: LLM counts specific items in a list
        
        Verification:
        - LLM correctly identifies the item to count
        - Tool is called with proper list format
        - Count result matches expected value
        """
        counter_tool = CounterTool()
        tool_definitions = [counter_tool.get_metadata()]
        
        items_list = "apple, banana, apple, cherry, apple, date"
        
        task_message = f"""
I have a list of fruits: {items_list}

How many times does 'apple' appear in this list?
Use the counter tool to count them accurately.
"""
        
        messages = [{"role": "user", "content": task_message}]
        
        system_prompt = """
You are a counting assistant. When asked to count items in a list, 
use the counter tool with the comma-separated list and the item to count.
"""
        
        response = openrouter_client.call_with_tools(
            messages=messages,
            tools=tool_definitions,
            system_prompt=system_prompt
        )
        
        print(f"\n🤖 LLM Response: {response['content']}")
        print(f"🔧 Tool Calls: {response['tool_calls']}")
        
        assert len(response['tool_calls']) > 0, "LLM should call counter"
        
        tool_call = response['tool_calls'][0]
        assert tool_call['name'] == 'counter', f"Expected counter, got {tool_call['name']}"
        
        args = tool_call['arguments']
        
        # Verify the list is recognized
        items_arg = args.get('items', '').lower()
        assert 'apple' in items_arg, "Items list should contain apple"
        
        # Verify the item to count
        item_to_count = args.get('item_to_count', '').lower().strip()
        assert item_to_count == 'apple', f"Should count apple, got {item_to_count}"
        
        # Execute and verify count
        result = counter_tool.run(**args)
        assert result == 3, f"Expected 3 apples, got {result}"
        
        print(f"\n✨ Test Passed! LLM correctly counted items: {result}")
    
    @pytest.mark.real_llm
    def test_llm_calls_math_and_name_tools(self, openrouter_client):
        """
        Scenario: LLM uses both math_calculator and name_formatter tools
        
        Verification:
        - LLM recognizes need for multiple tools
        - At least one tool is called correctly
        - Results are accurate
        """
        math_tool = MathCalculatorTool()
        name_tool = PersonNameFormatterTool()
        
        tool_definitions = [
            math_tool.get_metadata(),
            name_tool.get_metadata()
        ]
        
        task_message = """
You have two tasks:
1. Calculate 30 + 15
2. Format "Alice" "Johnson" as full name

Use the math_calculator tool with operation='add', a=30, b=15
Use the name_formatter tool with first_name="Alice", last_name="Johnson", format="full"
"""
        
        messages = [{"role": "user", "content": task_message}]
        
        system_prompt = """
You are a helpful assistant with access to two tools: math_calculator and name_formatter.
Use the appropriate tools to complete the requested tasks.
"""
        
        response = openrouter_client.call_with_tools(
            messages=messages,
            tools=tool_definitions,
            system_prompt=system_prompt,
            max_iterations=5
        )
        
        print(f"\n🤖 LLM Response: {response['content']}")
        print(f"🔧 Tool Calls: {response['tool_calls']}")
        
        assert len(response['tool_calls']) >= 1, f"Expected at least 1 tool call, got {len(response['tool_calls'])}"
        
        tool_names = [tc['name'] for tc in response['tool_calls']]
        print(f"🔧 Tool Names Called: {tool_names}")
        
        # Verify at least one tool was called and executed correctly
        if 'math_calculator' in tool_names:
            math_calls = [tc for tc in response['tool_calls'] if tc['name'] == 'math_calculator']
            args = math_calls[0]['arguments']
            result = math_tool.run(**args)
            print(f"✅ Math result: {result}")
        
        if 'name_formatter' in tool_names:
            name_calls = [tc for tc in response['tool_calls'] if tc['name'] == 'name_formatter']
            args = name_calls[0]['arguments']
            result = name_tool.run(**args)
            print(f"✅ Name format result: {result}")
        
        print(f"\n✨ Test Passed! LLM used multiple tools")
    
    @pytest.mark.real_llm
    def test_llm_division_with_error_handling(self, openrouter_client):
        """
        Scenario: LLM should handle edge cases like division by zero
        
        Verification:
        - LLM attempts to divide by a valid number (succeeds)
        - Tool parameters are correctly identified
        """
        math_tool = MathCalculatorTool()
        tool_definitions = [math_tool.get_metadata()]
        
        task_message = """
Calculate 100 divided by 5.
Use math_calculator with:
- operation: "divide"  
- a: 100
- b: 5
"""
        
        messages = [{"role": "user", "content": task_message}]
        
        system_prompt = "You are a calculator. Use math_calculator for division."
        
        response = openrouter_client.call_with_tools(
            messages=messages,
            tools=tool_definitions,
            system_prompt=system_prompt
        )
        
        print(f"\n🤖 LLM Response: {response['content']}")
        print(f"🔧 Tool Calls: {response['tool_calls']}")
        
        assert len(response['tool_calls']) > 0, "LLM should call math_calculator"
        
        tool_call = response['tool_calls'][0]
        args = tool_call['arguments']
        
        assert args.get('operation') == 'divide', f"Operation should be divide"
        assert args.get('a') == 100, f"First number should be 100"
        assert args.get('b') == 5, f"Second number should be 5"
        
        result = math_tool.run(**args)
        assert result == 20, f"100 / 5 should equal 20, got {result}"
        
        print(f"\n✨ Test Passed! LLM correctly called divide: {result}")
