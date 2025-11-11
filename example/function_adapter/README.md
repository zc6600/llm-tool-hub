# FunctionAdapter - Get Raw Python Functions

This directory contains examples of using FunctionAdapter to convert BaseTool instances to raw Python functions.

## What is FunctionAdapter?

FunctionAdapter is a lightweight adapter that converts BaseTool instances into simple, callable Python functions. Unlike LangChain or MCP adapters, it provides **zero-overhead** access to tool functionality - just pure Python functions.

## Why Use FunctionAdapter?

- **Simplicity**: Pure Python functions with no framework overhead
- **No dependencies**: Works with just the tool definitions
- **Easy integration**: Works with any Python code
- **Introspection**: Access to function metadata and parameters
- **Type preservation**: Functions maintain their original signatures

## Quick Start

### Basic Usage

```python
from llm_tool_hub.filesystem_tool.read_file_tool import ReadFileTool
from llm_tool_hub.integrations.function_adapter import FunctionAdapter

# Create tools
tools = [ReadFileTool()]

# Create adapter
adapter = FunctionAdapter(tools)

# Get the function
read_func = adapter.get_function("read_file")

# Use it like a regular Python function
result = read_func(file_path="data.txt")
print(result)
```

### Get All Functions

```python
# Get functions as a list
all_funcs = adapter.get_all_functions()

# Or as a dictionary
funcs_dict = adapter.get_functions_dict()

# Use it
result = funcs_dict["read_file"](file_path="data.txt")
```

### Dictionary-Style Access

```python
# Get function with bracket notation
read_func = adapter["read_file"]

# Check if function exists
if "read_file" in adapter:
    result = adapter["read_file"](file_path="data.txt")
```

### Call Through Adapter

```python
# Call directly through adapter
result = adapter.call_function("read_file", file_path="data.txt")
```

## API Reference

### Creating an Adapter

```python
from llm_tool_hub.integrations.function_adapter import FunctionAdapter

adapter = FunctionAdapter(tools)
```

### Getting Functions

| Method | Returns | Example |
|--------|---------|---------|
| `get_function(name)` | Single function or None | `func = adapter.get_function("read_file")` |
| `get_all_functions()` | List of functions | `funcs = adapter.get_all_functions()` |
| `get_functions_dict()` | Dict of name→function | `d = adapter.get_functions_dict()` |
| `adapter[name]` | Function (raises KeyError if not found) | `func = adapter["read_file"]` |

### Calling Functions

| Method | Description | Example |
|--------|-------------|---------|
| `call_function(name, **kwargs)` | Call through adapter | `adapter.call_function("read_file", file_path="x.txt")` |
| `func(**kwargs)` | Direct function call | `result = read_func(file_path="x.txt")` |

### Getting Information

| Method | Returns | Example |
|--------|---------|---------|
| `get_function_info(name)` | Dict with function metadata | `info = adapter.get_function_info("read_file")` |
| `get_all_function_info()` | Dict of name→info | `all_info = adapter.get_all_function_info()` |

### Utility Methods

| Method | Description | Example |
|--------|-------------|---------|
| `len(adapter)` | Number of functions | `count = len(adapter)` |
| `name in adapter` | Check if function exists | `if "read_file" in adapter:` |
| `repr(adapter)` | String representation | `print(adapter)` |

## Function Metadata

Each function has metadata attached:

```python
func = adapter["read_file"]

# Access metadata
print(func.__name__)          # "read_file"
print(func.__doc__)           # Full description
print(func.json_schema)       # Parameter schema
```

## Comparison with Other Adapters

| Feature | FunctionAdapter | LangChain | MCP |
|---------|-----------------|-----------|-----|
| Returns | Raw Python functions | LangChain tools | JSON-RPC server |
| Dependencies | None | LangChain library | MCP protocol |
| Use case | Simple Python integration | LLM frameworks | Standardized protocol |
| Overhead | Minimal | High | Protocol layer |
| Learning curve | Minimal | Medium | High |

## Use Cases

### 1. Simple Tool Integration

```python
adapter = FunctionAdapter(tools)
func = adapter["shell_tool"]
result = func(command="ls -la")
```

### 2. Batch Processing

```python
for file_path in file_list:
    result = adapter.call_function("read_file", file_path=file_path)
    process(result)
```

### 3. Tool Discovery

```python
all_info = adapter.get_all_function_info()
for name, info in all_info.items():
    print(f"{name}: {info['description']}")
```

### 4. Dynamic Function Mapping

```python
funcs = adapter.get_functions_dict()
operation = user_input  # e.g., "read_file"

if operation in funcs:
    result = funcs[operation](file_path="data.txt")
```

### 5. Integration with Existing Code

```python
# Add tool functionality to existing Python code
read_func = adapter["read_file"]
process_func = my_existing_processor
write_func = adapter["create_file"]

# Pipeline
data = read_func(file_path="input.txt")
processed = process_func(data)
write_func(file_path="output.txt", file_content=processed)
```

## Examples

Run the basic usage example:

```bash
python 01_basic_usage.py
```

## When to Use Each Adapter

- **FunctionAdapter**: You want pure Python functions
- **LangChainAdapter**: You're using LangChain or similar frameworks
- **MCPAdapter/MCPServer**: You want to expose tools via the Model Context Protocol (for Claude Desktop, VS Code, etc.)

## Notes

- FunctionAdapter preserves function signatures and metadata
- Functions are callable and behave like normal Python functions
- No external dependencies required
- All parameter validation happens in the tool's run() method
- Error handling is delegated to the underlying tool implementation
