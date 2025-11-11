# MCP (Model Context Protocol) Examples

This directory contains examples of using llm-tool-hub as an MCP server.

## What is MCP?

Model Context Protocol (MCP) is a standardized protocol that allows LLM applications (such as Claude, VS Code) to communicate with tools through a standardized interface.

## Quick Start

### 1. Basic Stdio Server (Simplest)

```bash
# Start the server
python 01_basic_stdio_server.py

# In another terminal, run the client
python 03_mcp_client.py
```

This will:

- Start an MCP server that accepts JSON-RPC commands
- List all available tools
- Call an example tool

### 2. Integration with Claude Desktop

Edit `~/.config/Claude/claude_desktop_config.json` (or `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "llm-tool-hub": {
      "command": "python",
      "args": ["/path/to/01_basic_stdio_server.py"]
    }
  }
}
```

Restart Claude Desktop, and you'll be able to use all llm-tool-hub tools in conversations.

### 3. Integration with VS Code

In VS Code settings:

```json
{
  "modelContextProtocol": {
    "servers": {
      "llm-tool-hub": {
        "command": "python",
        "args": ["/path/to/01_basic_stdio_server.py"]
      }
    }
  }
}
```

## File Description

- `01_basic_stdio_server.py` - Minimal MCP server implementation using standard input/output
- `03_mcp_client.py` - Test client for testing the server

## Protocol Details

### Message Format

All messages are JSON, one per line:

```json
{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
```

### Supported Methods

1. **initialize** - Initialize the connection

```json
{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"clientInfo": {"name": "Claude"}}}
```

2. **tools/list** - List all available tools

```json
{"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
```

3. **tools/call** - Call a tool

```json
{"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "search_semantic_scholar", "arguments": {"query": "AI"}}}
```

## Debugging

View server logs (output to stderr):

```bash
python 01_basic_stdio_server.py 2>&1 | tee server.log
```

## Next Steps

- Explore different tools (filesystem, shell, search, etc.)
- Customize tool configuration
- Integrate with SSE transport (HTTP mode)
