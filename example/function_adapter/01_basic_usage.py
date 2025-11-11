#!/usr/bin/env python3
# example/function_adapter/01_basic_usage.py

"""
Basic usage of FunctionAdapter

This example shows how to use FunctionAdapter to get raw Python functions
from BaseTool instances and use them directly without any framework.

FunctionAdapter is useful when you:
- Want pure Python functions without LangChain wrapping
- Need to integrate tools into existing Python code
- Want the simplest possible API
- Don't need framework-specific features
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from llm_tool_hub.filesystem_tool.read_file_tool import ReadFileTool
from llm_tool_hub.filesystem_tool.create_file_tool import CreateFileTool
from llm_tool_hub.shell_tool.shell_tool import ShellTool
from llm_tool_hub.integrations.function_adapter import FunctionAdapter


def main():
    """Demonstrate FunctionAdapter usage."""
    
    print("=" * 70)
    print("FunctionAdapter - Get Raw Python Functions from Tools")
    print("=" * 70)
    
    # Create some tools
    tools = [
        ReadFileTool(),
        CreateFileTool(),
        ShellTool(),
    ]
    
    # Create adapter
    adapter = FunctionAdapter(tools)
    
    # 1. Get a single function
    print("\n1. Getting a single function:")
    print("-" * 70)
    read_func = adapter.get_function("read_file")
    print(f"   Function name: {read_func.__name__}")
    print(f"   Function doc: {read_func.__doc__[:80]}...")
    print(f"   ✓ Got callable function: {callable(read_func)}")
    
    # 2. Get all functions
    print("\n2. Getting all functions:")
    print("-" * 70)
    all_functions = adapter.get_all_functions()
    print(f"   Total functions: {len(all_functions)}")
    for func in all_functions:
        print(f"   - {func.__name__}")
    
    # 3. Get functions as dictionary
    print("\n3. Getting functions as dictionary:")
    print("-" * 70)
    funcs_dict = adapter.get_functions_dict()
    for name, func in funcs_dict.items():
        print(f"   {name}: {type(func).__name__}")
    
    # 4. Call function directly
    print("\n4. Calling functions directly:")
    print("-" * 70)
    
    # Create a test file first
    create_func = adapter["create_file"]
    test_file = "/tmp/test_adapter.txt"
    create_result = create_func(file_path=test_file, content="Hello from FunctionAdapter!")
    print(f"   Created file: {test_file}")
    print(f"   Result: {create_result[:100]}...")
    
    # Now read it back
    read_result = read_func(file_path=test_file)
    print(f"\n   Read content: {read_result}")
    
    # 5. Get function information
    print("\n5. Getting function information:")
    print("-" * 70)
    shell_info = adapter.get_function_info("shell_tool")
    print(f"   Function: {shell_info['name']}")
    print(f"   Description: {shell_info['description'][:100]}...")
    print(f"   Parameters: {list(shell_info['parameters_json']['properties'].keys())}")
    
    # 6. Call function through adapter
    print("\n6. Calling through adapter.call_function():")
    print("-" * 70)
    shell_result = adapter.call_function("shell_tool", command="echo 'test' && date")
    print(f"   Command output:\n{shell_result[:200]}...")
    
    # 7. Using dictionary-style access
    print("\n7. Using dictionary-style access:")
    print("-" * 70)
    print(f"   Available functions: {list(adapter.get_functions_dict().keys())}")
    print(f"   'shell_tool' in adapter: {'shell_tool' in adapter}")
    print(f"   'nonexistent' in adapter: {'nonexistent' in adapter}")
    print(f"   Number of functions: {len(adapter)}")
    
    # 8. Function introspection
    print("\n8. Function introspection:")
    print("-" * 70)
    func = adapter["read_file"]
    print(f"   Name: {func.__name__}")
    print(f"   Docstring: {func.__doc__[:80]}...")
    print(f"   Has metadata: {hasattr(func, 'json_schema')}")
    if hasattr(func, 'json_schema'):
        schema = func.json_schema
        print(f"   Schema properties: {list(schema.get('properties', {}).keys())}")
    
    # 9. Get complete info for all functions
    print("\n9. Complete information for all functions:")
    print("-" * 70)
    all_info = adapter.get_all_function_info()
    for name, info in all_info.items():
        print(f"\n   {name}:")
        print(f"      Description: {info['description'][:70]}...")
        params = info['parameters_json']['properties']
        print(f"      Parameters: {list(params.keys())}")
    
    # 10. Adapter representation
    print("\n10. Adapter representation:")
    print("-" * 70)
    print(f"   {repr(adapter)}")
    
    print("\n" + "=" * 70)
    print("✓ FunctionAdapter examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
