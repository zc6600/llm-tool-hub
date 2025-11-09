# tests/real_llm/conftest.py

import pytest
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Any

load_dotenv()

# ============================================================================
# OpenRouter Client (Using OpenAI SDK)
# ============================================================================

class OpenRouterClient:
    """
    OpenRouter API client using OpenAI SDK.
    OpenRouter is compatible with OpenAI's Function Calling API.
    """
    
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model = model or os.getenv("OPENROUTER_MODEL", "openai/gpt-4-turbo")
        
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment")
        
        # Use OpenAI SDK pointing to OpenRouter endpoint
        from openai import OpenAI
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1"
        )
    
    def call_with_tools(self,
                       messages: List[Dict[str, str]],
                       tools: List[Dict[str, Any]],
                       system_prompt: str = None,
                       tool_executors: Dict[str, callable] = None,
                       max_iterations: int = 3) -> Dict[str, Any]:
        """
        Call OpenRouter API with tool support and execute tool calls.
        
        Args:
            messages: List of conversation messages
            tools: List of tool definitions in JSON Schema format
            system_prompt: System prompt
            tool_executors: Dict mapping tool names to executor functions
            max_iterations: Maximum number of tool use iterations
        
        Returns:
            {
                'content': str,           # LLM's final text response
                'tool_calls': [           # All tool calls made
                    {
                        'id': str,
                        'name': str,
                        'arguments': dict
                    }
                ],
                'raw_response': ...       # Raw API response
            }
        """
        # Construct initial message list
        all_messages = list(messages)
        if system_prompt:
            all_messages = [{"role": "system", "content": system_prompt}] + all_messages
        
        tool_executors = tool_executors or {}
        all_tool_calls = []
        
        # Agentic loop: Keep calling LLM until it stops wanting to use tools
        for iteration in range(max_iterations):
            # Call OpenRouter API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=all_messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=4096
            )
            
            # Parse response
            content = response.choices[0].message.content or ""
            tool_calls = []
            
            if response.choices[0].message.tool_calls:
                for tc in response.choices[0].message.tool_calls:
                    # Handle cases where OpenRouter concatenates multiple JSON objects
                    arguments_str = tc.function.arguments.strip()
                    arguments = None
                    
                    try:
                        # Try normal JSON parsing first
                        arguments = json.loads(arguments_str)
                    except json.JSONDecodeError:
                        # If that fails, try to parse multiple JSON objects
                        # This happens when the API concatenates {"a":1}{"b":2}
                        import re
                        json_objects = re.findall(r'\{[^}]+\}', arguments_str)
                        if json_objects:
                            # Merge all JSON objects into one
                            merged = {}
                            for obj_str in json_objects:
                                try:
                                    obj = json.loads(obj_str)
                                    merged.update(obj)
                                except json.JSONDecodeError:
                                    pass
                            if merged:
                                arguments = merged
                            else:
                                arguments = {}
                        else:
                            arguments = {}
                    
                    tool_calls.append({
                        'id': tc.id,
                        'name': tc.function.name,
                        'arguments': arguments
                    })
            
            all_tool_calls.extend(tool_calls)
            
            # Add assistant's response to messages
            all_messages.append({
                "role": "assistant",
                "content": content,
                "tool_calls": [
                    {
                        "id": tc['id'],
                        "type": "function",
                        "function": {
                            "name": tc['name'],
                            "arguments": json.dumps(tc['arguments'])
                        }
                    } for tc in tool_calls
                ] if tool_calls else None
            })
            
            # If no tool calls, we're done
            if not tool_calls:
                return {
                    'content': content,
                    'tool_calls': all_tool_calls,
                    'raw_response': response
                }
            
            # Execute tools and add results to messages
            for tool_call in tool_calls:
                tool_name = tool_call['name']
                tool_args = tool_call['arguments']
                
                if tool_name in tool_executors:
                    tool_result = tool_executors[tool_name](**tool_args)
                else:
                    tool_result = f"Tool '{tool_name}' not found in executors"
                
                all_messages.append({
                    "role": "user",
                    "content": f"Tool result for '{tool_name}':\n{tool_result}"
                })
        
        # Return final response
        return {
            'content': content,
            'tool_calls': all_tool_calls,
            'raw_response': response
        }

# ============================================================================
# Pytest Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def openrouter_client():
    """Initialize OpenRouter client (session scope)"""
    try:
        client = OpenRouterClient()
        print(f"\n✓ OpenRouter client initialized (Model: {client.model})")
        return client
    except ValueError as e:
        pytest.skip(f"OpenRouter initialization failed: {e}")


@pytest.fixture
def llm_tools(tmp_path: Path):
    """Initialize all tools"""
    from llm_tool_hub.filesystem_tool.create_file_tool import CreateFileTool
    from llm_tool_hub.filesystem_tool.read_file_tool import ReadFileTool
    from llm_tool_hub.filesystem_tool.modify_file_tool import ModifyFileTool
    
    # Initialize workspace
    (tmp_path / "workspace").mkdir(exist_ok=True)
    
    return {
        'create': CreateFileTool(root_path=tmp_path),
        'read': ReadFileTool(root_path=tmp_path),
        'modify': ModifyFileTool(root_path=tmp_path),
    }


@pytest.fixture
def tool_definitions(llm_tools):
    """Generate tool JSON Schema definitions for LLM"""
    tools_spec = []
    
    for tool_name, tool_instance in llm_tools.items():
        # Each tool should have get_metadata() method that returns OpenAI-compatible schema
        tools_spec.append(tool_instance.get_metadata())
    
    return tools_spec


@pytest.fixture
def sandbox_dir(tmp_path: Path):
    """Provide isolated working directory for each test"""
    return tmp_path
