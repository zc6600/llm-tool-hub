# MCP 集成文件结构方案

## 📁 完整的文件结构设计

```
llm-tool-hub/
├── src/llm_tool_hub/
│   ├── integrations/                          # 现有目录
│   │   ├── __init__.py
│   │   ├── langchain_adapter.py               # 现有文件
│   │   ├── tool_registry.py                   # 现有文件
│   │   ├── mcp_adapter.py                     # ✨ 新增 (核心适配器)
│   │   └── mcp_server.py                      # ✨ 新增 (MCP 服务器)
│   │
│   └── transports/                            # ✨ 新增目录 (传输层)
│       ├── __init__.py                        # ✨ 新增
│       ├── base_transport.py                  # ✨ 新增 (抽象基类)
│       ├── stdio_transport.py                 # ✨ 新增 (标准输入输出)
│       └── sse_transport.py                   # ✨ 新增 (Server-Sent Events)
│
├── tests/
│   ├── integrations/                          # 现有目录
│   │   ├── test_langchain_adapter.py          # 现有文件
│   │   ├── test_tool_registry.py              # 现有文件
│   │   ├── test_mcp_adapter.py                # ✨ 新增
│   │   └── test_mcp_server.py                 # ✨ 新增
│   │
│   └── transports/                            # ✨ 新增目录
│       ├── __init__.py                        # ✨ 新增
│       ├── test_stdio_transport.py            # ✨ 新增
│       └── test_sse_transport.py              # ✨ 新增
│
├── example/
│   └── mcp/                                   # ✨ 新增目录
│       ├── 01_basic_stdio_server.py           # ✨ 新增
│       ├── 02_sse_server.py                   # ✨ 新增
│       ├── 03_mcp_client.py                   # ✨ 新增
│       └── README.md                          # ✨ 新增
│
└── docs/
    ├── MCP_INTEGRATION_PLAN.md                # ✨ 新增 (已创建)
    ├── MCP_QUICK_START.md                     # ✨ 新增
    └── MCP_DEPLOYMENT.md                      # ✨ 新增
```

---

## 📊 文件创建优先级和顺序

### 第 1 阶段：核心实现（关键路径）

| 优先级 | 文件 | 行数 | 难度 | 说明 |
|--------|------|------|------|------|
| 🔴 P1 | `mcp_adapter.py` | 150-200 | ⭐⭐ | 核心适配器，必须先做 |
| 🔴 P1 | `base_transport.py` | 50-80 | ⭐ | 抽象基类 |
| 🟡 P2 | `stdio_transport.py` | 100-150 | ⭐⭐ | 本地模式 |
| 🟡 P2 | `mcp_server.py` | 200-250 | ⭐⭐⭐ | 依赖于 adapter |
| 🟡 P2 | `sse_transport.py` | 150-200 | ⭐⭐⭐ | HTTP 模式 |

### 第 2 阶段：测试（完整性保证）

| 优先级 | 文件 | 行数 | 说明 |
|--------|------|------|------|
| 🟡 P2 | `test_mcp_adapter.py` | 200-250 | 单元测试 |
| 🟡 P2 | `test_stdio_transport.py` | 150-200 | 集成测试 |
| 🟡 P2 | `test_mcp_server.py` | 300-350 | 完整流程测试 |

### 第 3 阶段：示例和文档

| 优先级 | 文件 | 行数 | 说明 |
|--------|------|------|------|
| 🟢 P3 | `01_basic_stdio_server.py` | 50-100 | 最小示例 |
| 🟢 P3 | `02_sse_server.py` | 80-120 | HTTP 示例 |
| 🟢 P3 | `03_mcp_client.py` | 100-150 | 客户端示例 |
| 🟢 P3 | 文档文件 | 500-800 | 指南和部署 |

---

## 🎯 详细的文件说明

### 核心文件详解

#### 1️⃣ `mcp_adapter.py` (必先做)
**职责**: 将 BaseTool 转换为 MCP 兼容格式

**关键类**:
```python
class MCPAdapter:
    - __init__(tools: List[BaseTool])
    - get_mcp_tools() -> List[MCPTool]
    - execute(name: str, args: dict) -> str
    - to_mcp_schema(tool: BaseTool) -> dict
```

**依赖**: 无（只依赖 BaseTool）

**测试**: 单元测试，纯 mock

---

#### 2️⃣ `base_transport.py` (基础设施)
**职责**: 定义传输层抽象接口

**关键类**:
```python
class BaseTransport(ABC):
    - async start()
    - async stop()
    - async send(message: dict)
    - async receive() -> dict
```

**依赖**: 无（纯抽象）

**用途**: 被 stdio_transport 和 sse_transport 继承

---

#### 3️⃣ `stdio_transport.py` (本地传输)
**职责**: 实现标准输入输出传输

**关键类**:
```python
class StdioTransport(BaseTransport):
    - async start()  # 启动读写循环
    - async stop()   # 关闭
    - async send(msg)
    - async receive()
```

**依赖**: BaseTransport

**特性**:
- 用于本地命令行工具
- 与 VS Code, Claude Desktop 兼容

---

#### 4️⃣ `mcp_server.py` (核心业务逻辑)
**职责**: 组装 MCP 服务器

**关键类**:
```python
class ToolHubMCPServer:
    - __init__(tools: List[BaseTool], transport: BaseTransport)
    - async run()
    - async handle_list_tools()
    - async handle_call_tool(name, args)
```

**依赖**: MCPAdapter, BaseTransport

**职责**:
- 处理 MCP JSON-RPC 协议
- 调用工具
- 返回结果

---

#### 5️⃣ `sse_transport.py` (HTTP 传输)
**职责**: 实现 Server-Sent Events 传输

**关键类**:
```python
class SSETransport(BaseTransport):
    - async start()        # 启动 Uvicorn 服务器
    - async stop()         # 关闭
    - create_fastapi_app() # 创建 FastAPI 应用
```

**依赖**: BaseTransport, FastAPI, Uvicorn

**特性**:
- HTTP 双向通信
- 支持跨网络

---

### 测试文件详解

#### `test_mcp_adapter.py`
```python
# 测试内容:
- test_adapter_initialization()
- test_single_tool_conversion()
- test_multiple_tools_conversion()
- test_execute_existing_tool()
- test_execute_nonexistent_tool()
- test_schema_format_compliance()
```

#### `test_mcp_server.py`
```python
# 测试内容:
- test_server_initialization()
- test_list_tools_request()
- test_call_tool_request()
- test_error_handling()
- test_concurrent_calls()
```

---

## 📋 创建步骤检查清单

### ✅ Step 1: 创建目录结构
```bash
mkdir -p src/llm_tool_hub/transports
mkdir -p tests/transports
mkdir -p example/mcp
```

### ✅ Step 2: 创建核心文件（顺序很重要）
1. [ ] `__init__.py` (transports 目录)
2. [ ] `base_transport.py`
3. [ ] `mcp_adapter.py`
4. [ ] `stdio_transport.py`
5. [ ] `mcp_server.py`
6. [ ] `sse_transport.py` (可选，先不做)

### ✅ Step 3: 创建测试文件
1. [ ] `__init__.py` (tests/transports 目录)
2. [ ] `test_mcp_adapter.py`
3. [ ] `test_stdio_transport.py`
4. [ ] `test_mcp_server.py`

### ✅ Step 4: 创建示例文件
1. [ ] `01_basic_stdio_server.py`
2. [ ] `03_mcp_client.py`

### ✅ Step 5: 文档
1. [ ] `MCP_QUICK_START.md`

---

## 🔗 文件依赖关系

```
无依赖
  ↓
base_transport.py
  ↓
mcp_adapter.py
  ↓
stdio_transport.py
  ↓
mcp_server.py
```

---

## 💾 新增依赖包

需要添加到 `pyproject.toml`:

```toml
[project.optional-dependencies]
mcp = [
    "mcp>=0.4.0",
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
    "httpx>=0.25.0",
]
```

或者用 `requirements-mcp.txt`:
```
mcp>=0.4.0
fastapi>=0.104.0
uvicorn>=0.24.0
httpx>=0.25.0
```

---

## 🎓 建议的实现顺序

### 第一周：核心实现
- **Day 1**: 创建目录 + base_transport.py
- **Day 2**: mcp_adapter.py
- **Day 3**: stdio_transport.py
- **Day 4**: mcp_server.py
- **Day 5**: 基本测试

### 第二周：测试和示例
- **Day 1**: 完整测试套件
- **Day 2**: 示例脚本
- **Day 3**: 文档
- **Day 4**: 优化和 bug 修复

---

## 🚀 快速启动方案

如果你想快速看到效果，可以这样做：

### 最小可行产品 (MVP) 版本 - 只需 3 个文件

```
src/llm_tool_hub/
├── mcp_simple.py           # 简化版，包含所有逻辑
└── transports/
    └── __init__.py
```

然后逐步拆分为完整的模块化设计。

---

## 📝 下一步行动

你想从哪里开始?

1. **立即开始** - 我来创建所有文件框架
2. **先审视细节** - 先看一个核心文件的完整实现
3. **讨论架构** - 确认设计思路

你的选择是?
