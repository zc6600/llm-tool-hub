# MCP (Model Context Protocol) 集成方案

## 📋 项目现状分析

### 优势
1. **模块化架构**: 基于 `BaseTool` 抽象类，所有工具统一接口
2. **JSON Schema 标准**: 工具元数据已符合 JSON Schema 规范
3. **LangChain 集成**: 已有成熟的适配器模式
4. **丰富的工具集**: 文件系统、Shell、科研搜索等

### 现有集成方式
- ✅ 原生 Python 调用
- ✅ LangChain `StructuredTool`
- ⏳ 需要: MCP 协议支持

---

## 🔗 MCP 协议介绍

### 什么是 MCP?
Model Context Protocol 是 Anthropic 提出的通用协议，用于 **LLM 与工具之间的标准化通信**。

### MCP 的三层架构
```
┌─────────────────────────────┐
│    LLM Client              │  (Claude, GPT, etc.)
│    (VS Code, IDE, etc.)    │
└──────────────┬──────────────┘
               │ MCP Protocol
               │ (JSON-RPC over stdio/SSE)
┌──────────────▼──────────────┐
│    Tool Registry Service    │  (我们要构建的部分)
│    (MCP Server)             │
└──────────────┬──────────────┘
               │ Python API
┌──────────────▼──────────────┐
│    llm-tool-hub             │  (现有工具库)
│    (BaseTool 实例)          │
└─────────────────────────────┘
```

### MCP 关键特性
| 特性 | 说明 |
|------|------|
| **Tools** | 暴露工具定义和执行 |
| **Resources** | 提供访问代码库、文档等 |
| **Prompts** | 预定义的 LLM 提示词 |
| **Sampling** | LLM 扩展功能 |
| **Transport** | stdio, SSE, WebSocket |

---

## 🎯 集成设计方案

### 方案对比

#### 方案 A: 直接实现 MCP Server (推荐)
**优点:**
- 完全控制，零依赖
- 支持 stdio 和 SSE 传输
- 与现有 `BaseTool` 完全兼容

**缺点:**
- 需要从零实现 JSON-RPC 层
- 代码量较大

**代码量:** ~800 行

---

#### 方案 B: 使用 `mcp` 官方库
```bash
pip install mcp
```

**优点:**
- 官方支持，更稳定
- 更少的代码（~200 行）
- 自动处理 JSON-RPC

**缺点:**
- 引入新依赖
- 版本兼容性风险

**代码量:** ~200 行

---

#### 方案 C: 混合方案 (最佳实践)
- 使用官方 `mcp` 库快速原型
- 逐步优化为自定义实现
- 保持向后兼容

**推荐:** ✅ **方案 C**

---

## 📦 实现步骤

### Phase 1: 基础 MCP 适配器 (1-2天)
```
src/llm_tool_hub/
├── integrations/
│   ├── mcp_adapter.py          # MCP 适配器 (核心)
│   └── mcp_server.py           # MCP Server 实现
└── transports/                 # 新增目录
    ├── stdio_transport.py      # stdio 传输层
    └── sse_transport.py        # SSE 传输层
```

### Phase 2: 测试和示例 (3-5天)
```
tests/
├── integrations/
│   └── test_mcp_adapter.py     # MCP 适配器测试
└── mcp_examples/
    ├── stdio_server.py         # stdio 示例服务器
    └── sse_server.py           # SSE 示例服务器

example/
└── mcp/
    ├── 01_basic_server.ipynb   # 基础使用
    ├── 02_custom_tools.ipynb   # 自定义工具
    └── 03_client_integration.ipynb # 客户端集成
```

### Phase 3: 文档和优化 (2-3天)
```
docs/
├── MCP_QUICK_START.md
├── MCP_SERVER_DEPLOYMENT.md
└── MCP_CLIENT_EXAMPLES.md
```

---

## 💻 核心实现预览

### 1. MCP 适配器核心接口
```python
# src/llm_tool_hub/integrations/mcp_adapter.py

from typing import List, Dict, Any
from ..base_tool import BaseTool

class MCPAdapter:
    """Convert BaseTool instances to MCP-compatible format"""
    
    def __init__(self, tools: List[BaseTool]):
        self.tools = {tool.name: tool for tool in tools}
    
    def to_mcp_tool_schema(self, tool: BaseTool) -> Dict[str, Any]:
        """转换为 MCP Tool Schema"""
        return {
            "name": tool.name,
            "description": tool.description,
            "inputSchema": {
                "type": "object",
                "properties": tool.parameters.get("properties", {}),
                "required": tool.parameters.get("required", [])
            }
        }
    
    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """执行工具"""
        if name not in self.tools:
            raise ValueError(f"Unknown tool: {name}")
        
        tool = self.tools[name]
        return tool.run(**arguments)
```

### 2. MCP Server 实现
```python
# src/llm_tool_hub/integrations/mcp_server.py

from mcp.server import Server
from mcp.types import Tool, TextContent
from typing import List
from ..base_tool import BaseTool

class ToolHubMCPServer:
    def __init__(self, tools: List[BaseTool]):
        self.server = Server("llm-tool-hub")
        self.adapter = MCPAdapter(tools)
        self._register_handlers()
    
    def _register_handlers(self):
        """Register MCP handlers"""
        @self.server.list_tools()
        async def list_tools():
            return [
                Tool(
                    name=tool.name,
                    description=tool.description,
                    inputSchema=self.adapter.to_mcp_tool_schema(tool)
                )
                for tool in self.adapter.tools.values()
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict):
            result = await self.adapter.execute_tool(name, arguments)
            return [TextContent(type="text", text=result)]
    
    def run_stdio(self):
        """Run over stdio transport"""
        import sys
        self.server.run(sys.stdin.buffer, sys.stdout.buffer)
    
    def run_sse(self, host: str = "127.0.0.1", port: int = 8000):
        """Run over SSE transport"""
        import uvicorn
        app = create_sse_app(self.server)
        uvicorn.run(app, host=host, port=port)
```

### 3. 快速启动脚本
```python
# 创建 MCP 服务器很简单:

from llm_tool_hub.filesystem_tool import *
from llm_tool_hub.shell_tool import ShellTool
from llm_tool_hub.scientific_research_tool import SearchSemanticScholar
from llm_tool_hub.integrations.mcp_server import ToolHubMCPServer

# 初始化工具
tools = [
    CreateFileTool(),
    ReadFileTool(),
    ModifyFileTool(),
    ShellTool(),
    SearchSemanticScholar(),
]

# 创建 MCP 服务器
server = ToolHubMCPServer(tools)

# 运行 stdio 模式 (用于 VS Code, Claude)
server.run_stdio()

# 或 SSE 模式 (HTTP)
# server.run_sse()
```

---

## 🔌 集成场景

### 场景 1: VS Code 集成
```json
// .vscode/settings.json
{
  "modelContextProtocol": {
    "servers": {
      "llm-tool-hub": {
        "command": "python",
        "args": ["-m", "llm_tool_hub.integrations.mcp_server"],
        "env": {
          "TOOL_CONFIG": "production.json"
        }
      }
    }
  }
}
```

### 场景 2: Claude Desktop (Mac/Windows)
```json
// ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "llm-tool-hub": {
      "command": "uv",
      "args": ["run", "python", "-m", "llm_tool_hub.integrations.mcp_server"]
    }
  }
}
```

### 场景 3: LangChain + MCP
```python
from llm_tool_hub.integrations.mcp_server import ToolHubMCPServer
from llm_tool_hub.integrations.langchain_adapter import LangchainToolAdapter

# 启动 MCP 服务器 (后台)
server = ToolHubMCPServer(tools)
asyncio.create_task(server.run_sse())

# 在 LangChain 中同时支持两种接口
langchain_tools = LangchainToolAdapter.to_langchain_structured_tool(tools)
```

---

## 📊 实现时间表

| Phase | 任务 | 预计时间 | 难度 |
|-------|------|---------|------|
| 1 | 基础 MCP 适配器 | 1-2天 | ⭐⭐ |
| 2 | 完整测试套件 | 2-3天 | ⭐⭐⭐ |
| 3 | 文档和示例 | 2-3天 | ⭐ |
| 4 | 性能优化 | 1-2天 | ⭐⭐⭐⭐ |
| 5 | 生产部署 | 1-2天 | ⭐⭐⭐ |

**总计:** 7-12 天

---

## ✅ 检查清单

### 前期准备
- [ ] 安装 MCP SDK: `pip install mcp`
- [ ] 阅读 MCP 官方文档
- [ ] 测试 MCP 样例

### Phase 1 实现
- [ ] 实现 `MCPAdapter` 类
- [ ] 实现 `ToolHubMCPServer` 类
- [ ] 实现 stdio 传输
- [ ] 基本单元测试

### Phase 2 测试
- [ ] 集成测试 (MCP 协议)
- [ ] 与 VS Code 集成测试
- [ ] 性能压力测试
- [ ] 文档完整性检查

### Phase 3 部署
- [ ] PyPI 发布准备
- [ ] CI/CD 流程
- [ ] 向后兼容性验证

---

## 🔗 参考资源

1. **MCP 官方文档**: https://modelcontextprotocol.io/
2. **MCP Python SDK**: https://github.com/anthropics/python-sdk
3. **MCP Examples**: https://github.com/modelcontextprotocol/servers
4. **JSON-RPC 2.0**: https://www.jsonrpc.org/specification

---

## 💡 建议优先级

1. ✅ **立即开始**: Phase 1 基础适配器
2. 📅 **两周内完成**: 完整实现和测试
3. 🚀 **生产发布**: 写完文档后发布

---

## 📝 下一步行动

你想从哪个部分开始?

- [ ] Phase 1: 实现基础 MCP 适配器
- [ ] Phase 2: 编写测试用例
- [ ] Phase 3: 创建文档
- [ ] 全部: 完整实现

建议: **先完成 Phase 1 的基础实现** (1-2天)，然后可以快速测试和迭代。
