# llm-tool-hub

> **Tools optimized for AI agents** - Reliable, agent-aware tool implementations for building robust autonomous systems.

[![Python Version](https://img.shields.io/badge/python-3.8+-blue)](https://www.python.org/downloads/)

[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🎯 What is llm-tool-hub?

**llm-tool-hub** is a Python library providing production-ready tools designed specifically for AI agents. Unlike generic tool wrappers, these tools are **optimized for agent interactions** with:

- ✅ **Agent-aware design**: Tools understand how LLMs call them
- ✅ **Consistent output formats**: Reliable for LLM parsing
- ✅ **Error resilience**: Built-in recovery mechanisms
- ✅ **Framework agnostic**: Works with any LLM framework
- ✅ **LangChain integration**: Native support via structured tools

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/zc6600/llm-tool-hub.git
cd llm-tool-hub

# Install the package
pip install .

# (Optional) Install with development dependencies for running tests
pip install ".[dev]"
```

### Basic Usage

```python
from llm_tool_hub.filesystem_tool.create_file_tool import CreateFileTool
from llm_tool_hub.filesystem_tool.read_file_tool import ReadFileTool

# Initialize tools
create_tool = CreateFileTool(root_path="/workspace")
read_tool = ReadFileTool(root_path="/workspace")

# Create a file
result = create_tool.run(
    file_path="hello.txt",
    content="Hello, World!",
    return_content=True
)
print(result)

# Read the file
result = read_tool.run(file_path="hello.txt")
print(result)
```

### LangChain Integration

```python
from llm_tool_hub.integrations.langchain_adapter import LangchainToolAdapter

# Convert to LangChain StructuredTool
lc_tool = LangchainToolAdapter.to_langchain_structured_tool(create_tool)

# Use with LangChain agents
agent = initialize_agent([lc_tool], llm, agent_type="structured-chat")
```

## 📚 Available Tools

### Filesystem Tools

#### 1. CreateFileTool

**Purpose**: Create new files with content

**Input Parameters**:

-`file_path` (str): Relative path to the new file

-`content` (str): Content to write

-`return_content` (bool): Whether to return content with line numbers (default: True)

**Output Format**:

```

SUCCESS: File 'example.py' successfully created with 10 lines of initial content.

Content with line numbers for subsequent modification:

--------------------------------------------------------------------------

1:def hello():

2:    print("Hello, World!")

--------------------------------------------------------------------------

```

**Example**:

```python

result = create_tool.run(

    file_path="script.py",

    content="def main():\n    pass\n"

)

```

---

#### 2. ReadFileTool

**Purpose**: Read file contents with optional line range support

**Input Parameters**:

-`file_path` (str): Relative path to the file

-`start_line` (int): Starting line number (1-indexed, default: 1)

-`end_line` (int): Ending line number (1-indexed, exclusive, default: None)

**Output Format**:

```

1:def hello():

2:    print("Hello")

3:

4:def goodbye():

5:    print("Goodbye")

```

**Example**:

```python

# Read entire file

result = read_tool.run(file_path="script.py")


# Read specific lines

result = read_tool.run(file_path="script.py", start_line=1, end_line=3)

```

---

#### 3. ModifyFileTool

**Purpose**: Modify existing file content (replace/insert/delete lines)

**Input Parameters**:

-`file_path` (str): Relative path to the file

-`start_line` (int): Starting line number (1-indexed)

-`end_line` (int): Ending line number (1-indexed)

-`new_content` (str): New content to insert

**Modes of Operation**:

-**Replace**: `start_line == end_line` - Replace a single line

-**Delete**: `new_content = ""` - Delete lines

-**Insert**: `end_line < start_line` - Insert before start_line

**Output Format**:

```

SUCCESS: File 'script.py' modified. Lines 2-2 replaced.

Updated content:

--------------------------------------------------------------------------

1:def hello(name):

2:    print(f"Hello, {name}!")

3:

4:def goodbye():

5:    print("Goodbye")

--------------------------------------------------------------------------

```

**Example**:

```python

# Replace line 2

result = modify_tool.run(

    file_path="script.py",

    start_line=2,

    end_line=2,

    new_content='    print("Modified")\n'

)


# Insert new lines after line 3

result = modify_tool.run(

    file_path="script.py",

    start_line=4,

    end_line=3,

    new_content='def new_func():\n    pass\n'

)


# Delete lines 2-3

result = modify_tool.run(

    file_path="script.py",

    start_line=2,

    end_line=3,

    new_content=""

)

```

---

### Shell Tool

#### 4. ShellTool

**Purpose**: Execute shell commands safely

**Input Parameters**:

-`command` (str): Shell command to execute

**Output Format**:

```

--- SHELL COMMAND RESULT ---

STATUS: SUCCESS

COMMAND: ls -la

OUTPUT:

total 48

drwxr-xr-x   5 user  group   160 Oct 28 10:00 .

drwxr-xr-x  15 user  group   480 Oct 28 10:00 ..

-rw-r--r--   1 user  group  1234 Oct 28 10:00 file.txt

```

**Example**:

```python

result = shell_tool.run(command="ls -la")

print(result)

```

---

## 🔌 Integration with AI Frameworks

### Direct Import (Minimal Setup)

```python

from llm_tool_hub.filesystem_tool.create_file_tool import CreateFileTool


tool = CreateFileTool(root_path="/workspace")

result = tool.run(file_path="test.txt", content="Hello")

print(result)

```

**Best for**: Simple scripts, direct tool usage, minimal dependencies

### LangChain Integration (Agent Ready)

```python

from llm_tool_hub.integrations.langchain_adapter import LangchainToolAdapter

from langchain.agents import initialize_agent


tools = [

    CreateFileTool(root_path="/workspace"),

    ReadFileTool(root_path="/workspace"),

]


lc_tools = [

    LangchainToolAdapter.to_langchain_structured_tool(t) for t in tools

]


agent = initialize_agent(lc_tools, llm, agent_type="structured-chat")

```

**Best for**: AI agents, LLM-driven automation, complex workflows

---

## 📖 Documentation

For detailed documentation, see:

-**[Usage Guide](example/usage_guide.ipynb)** - Interactive Jupyter notebook with examples

-**[API Documentation](docs/manual/)** - Detailed API reference

-**[Examples](example/)** - More code examples

---

## 🧪 Testing

### Run All Tests

```bash

pytest tests/-v

```

### Run Real LLM Tests (requires OpenRouter API key)

```bash

export OPENROUTER_API_KEY="your-key"

export OPENROUTER_MODEL="google/gemini-2.5-flash-lite-preview-09-2025"

pytest tests/real_llm/-v-mreal_llm

```

### Test Coverage

- ✅ Unit tests for all tools
- ✅ LangChain integration tests
- ✅ Real LLM integration tests with OpenRouter
- ✅ Shell command execution tests
- ✅ Error handling tests

---

## 🏗️ Project Structure

```

llm-tool-hub/

├── src/llm_tool_hub/

│   ├── base_tool.py                 # Base class for all tools

│   ├── tool_registry.py             # Tool registry system

│   ├── filesystem_tool/             # File operations

│   │   ├── create_file_tool.py

│   │   ├── read_file_tool.py

│   │   ├── modify_file_tool.py

│   │   └── base_filesystem_tool.py

│   ├── shell_tool/                  # Shell commands

│   │   └── shell_tool.py

│   └── integrations/                # Framework integrations

│       └── langchain_adapter.py

├── tests/                           # Test suite

│   ├── filesystem_tool/             # Filesystem tool tests

│   ├── shell_tool/                  # Shell tool tests

│   ├── integrations/                # Integration tests

│   └── real_llm/                    # Real LLM API tests

├── example/                         # Usage examples

│   └── usage_guide.ipynb            # Interactive notebook

├── docs/                            # Documentation

│   └── manual/                      # Detailed guides

└── README.md

```

---

## 🔐 Security Considerations

### Path Validation

All filesystem tools validate paths to prevent directory traversal:

```python

# ✅ Safe - within root_path

create_tool.run(file_path="data/file.txt", content="...")


# ❌ Blocked - attempts directory traversal

create_tool.run(file_path="../../../etc/passwd", content="...")

```

### Shell Command Sanitization

Be cautious when using ShellTool with untrusted input:

```python

# ✅ Safe - known command

shell_tool.run(command="ls -la")


# ⚠️ Risky - user input without validation

shell_tool.run(command=user_input)

```

**Recommendations**:

- Always validate user input before passing to tools
- Use `root_path` to restrict filesystem access
- Consider using restricted shells for ShellTool
- Run agents in isolated environments

---

## 💡 Best Practices for AI Agents

### 1. Error Handling

All tools return formatted strings. Check for errors:

```python

result = tool.run(...)

if result.startswith("ERROR:") or result.startswith("UNEXPECTED ERROR:"):

# Handle error

    print(f"Tool failed: {result}")

else:

# Process result

    print(result)

```

### 2. Context Management

Use line ranges to keep token usage manageable:

```python

# Instead of reading entire large file

result = read_tool.run(file_path="large_file.py")  # ❌ High token cost


# Read specific sections

result = read_tool.run(file_path="large_file.py", start_line=1, end_line=50)  # ✅

```

### 3. Batch Operations

Combine multiple operations efficiently:

```python

# Create files before reading them

create_tool.run(file_path="config.json", content=config)

result = read_tool.run(file_path="config.json")

```

### 4. Tool Metadata

Access tool definitions for agent integration:

```python

metadata = tool.get_metadata()

# Returns OpenAI Function Calling format

print(metadata)

# {

#     "type": "function",

#     "function": {

#         "name": "create_file",

#         "description": "...",

#         "parameters": {...}

#     }

# }

```

---

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details

---

## 🙋 Support

-**Issues**: Report bugs on GitHub Issues

-**Discussions**: Join discussions on GitHub Discussions

-**Documentation**: Check docs/ for detailed guides

---

## 🎓 Learning Resources

- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [LangChain Tools Documentation](https://python.langchain.com/docs/modules/tools/)
- [Building AI Agents](https://example.com/building-ai-agents)

---

**Made with ❤️ for AI agent developers**

*Last Updated: October 28, 2025*
