# ShellTool Timeout 处理机制详解

## 📋 概述

ShellTool 通过 `subprocess.run()` 的 `timeout` 参数实现对长时间运行命令的控制。

---

## 🔧 Timeout 参数定义

### 参数规格 (Parameters)

```python
"timeout": {
    "type": "integer",
    "description": f"Optional: Max time in seconds to wait for the command to complete. Defaults to {DEFAULT_TIMEOUT}.",
    "default": DEFAULT_TIMEOUT,  # 默认值: 100 秒
    "minimum": 1
}
```

**关键特征:**
- **类型**: `integer` (整数秒数)
- **默认值**: 100 秒
- **最小值**: 1 秒
- **可选**: 不在 `required` 列表中，可以省略

---

## 🎯 Timeout 处理流程

### 1️⃣ 命令执行阶段

```python
process = subprocess.run(
    command, 
    shell=True, 
    capture_output=True, 
    timeout=timeout,  # ← 这里传递 timeout 参数
    cwd=getattr(self, 'root_path', None),
    ...
)
```

**执行逻辑:**
- Python 等待命令完成
- 如果命令在 `timeout` 秒内完成 → 正常处理
- 如果超过 `timeout` 秒 → 抛出 `subprocess.TimeoutExpired` 异常

---

### 2️⃣ 正常完成 (无超时)

```
┌─────────────────────────────────────┐
│ subprocess.run(timeout=100)         │
├─────────────────────────────────────┤
│ ✓ 命令在 100 秒内完成              │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│ 返回 SUCCESS 或 ERROR               │
│ 状态取决于 returncode               │
├─────────────────────────────────────┤
│ returncode == 0 → STATUS: SUCCESS   │
│ returncode != 0 → STATUS: ERROR     │
└─────────────────────────────────────┘
```

**代码:**
```python
status = "SUCCESS" if process.returncode == 0 else "ERROR"

return self._format_result(
    command=command,
    status=status,
    returncode=process.returncode,
    stdout=stdout_truncated,
    stderr=stderr_truncated,
    warning=warning
)
```

---

### 3️⃣ 超时处理 (Timeout 发生)

```
┌─────────────────────────────────────┐
│ subprocess.run(timeout=100)         │
├─────────────────────────────────────┤
│ ✗ 100 秒后仍未完成 → 触发 timeout  │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│ subprocess.TimeoutExpired 异常      │
│ - 进程被终止                        │
│ - 保存部分输出 (partial output)    │
└─────────────────────────────────────┘
```

**关键特性:**
- 异常对象包含部分输出: `e.stdout`, `e.stderr`
- 进程被强制终止
- 部分输出被保存并返回给 LLM

**代码:**
```python
except subprocess.TimeoutExpired as e:
    # 提取部分输出
    partial_stdout = e.stdout if e.stdout else "No partial stdout captured."
    partial_stderr = e.stderr if e.stderr else "No partial stderr captured."
    
    # 截断输出
    stdout_truncated, stdout_warning = _truncate_output(partial_stdout)
    stderr_truncated, stderr_warning = _truncate_output(partial_stderr)
    
    # 返回 TIMEOUT_ERROR 状态
    return self._format_result(
        command=command,
        status="TIMEOUT_ERROR",
        returncode=-1,  # -1 表示 timeout
        stdout=stdout_truncated,
        stderr=stderr_truncated,
        warning=f"Command timed out after {timeout}s. Partial output captured. {warning}"
    )
```

---

## 📊 返回状态对照表

| 情况 | STATUS | RETURN_CODE | 说明 |
|------|--------|-------------|------|
| 命令成功执行 | SUCCESS | 0 | 命令正常完成，exit code = 0 |
| 命令执行失败 | ERROR | >0 | 命令出错，exit code 非零 |
| 命令超时 | TIMEOUT_ERROR | -1 | 命令超过 timeout 时限被终止 |
| 系统异常 | FATAL_ERROR | -2 | Python 执行异常（如权限错误） |

---

## ⏱️ Timeout 的实际行为

### 场景 1: 快速命令 (< timeout)

```python
# LLM 调用
shell_tool.run(command="echo hello", timeout=100)

# 执行
$ echo hello
hello
# 耗时: ~0.1 秒

# 返回
STATUS: SUCCESS
RETURN_CODE: 0
STDOUT: hello
```

---

### 场景 2: 长时间运行命令 (> timeout)

```python
# LLM 调用
shell_tool.run(command="sleep 300", timeout=5)

# 执行
$ sleep 300
# 运行 5 秒后 → subprocess 强制终止

# 返回
STATUS: TIMEOUT_ERROR
RETURN_CODE: -1
STDOUT: (空，因为 sleep 无输出)
STDERR: 
WARNING: Command timed out after 5s. Partial output captured.
```

---

### 场景 3: 超时但有部分输出

```python
# LLM 调用
shell_tool.run(command="python long_script.py", timeout=3)

# 执行
$ python long_script.py
Processing item 1...    # 输出
Processing item 2...    # 输出
Processing item 3...    # 此时 3 秒到达，进程被终止

# 返回
STATUS: TIMEOUT_ERROR
RETURN_CODE: -1
STDOUT: Processing item 1...
        Processing item 2...
        Processing item 3...
WARNING: Command timed out after 3s. Partial output captured.
```

---

## 🛡️ 安全机制

### 1. 强制终止
- `subprocess.run()` 在 timeout 触发时会**强制杀死进程**
- 不是温和的 SIGTERM，是硬关闭
- 保证了长时间运行的命令不会让 LLM 等待

### 2. 部分输出保留
- 即使超时，也会尝试捕获已产生的输出
- LLM 可以看到命令执行到了哪里
- 有助于调试和了解执行进度

### 3. 输出截断
- 除了 timeout 限制外，还有 `MAX_OUTPUT_LENGTH` 限制
- 防止超大输出占用资源
- 如果超时 + 输出很长 → 两层截断都会应用

---

## 💡 使用建议

### 对于 LLM Agent

```python
# ✓ 快速命令 - 使用默认超时
response = shell_tool.run(command="ls -la src/")

# ✓ 中等命令 - 自定义较长超时
response = shell_tool.run(
    command="git clone https://...", 
    timeout=30
)

# ✓ 长时间命令 - 设置足够的超时
response = shell_tool.run(
    command="python data_processing.py",
    timeout=300  # 5 分钟
)
```

### 处理 Timeout 响应

```python
# LLM 接收到响应后的处理逻辑
if "TIMEOUT_ERROR" in response:
    # 策略 1: 重试更长的 timeout
    response = shell_tool.run(
        command=original_command,
        timeout=timeout * 2  # 加倍超时时间
    )
    
    # 策略 2: 分解任务
    # 将大任务分解成小任务，分别执行
    
    # 策略 3: 使用后台处理
    # 告诉 LLM 这个任务太长，需要异步处理
```

---

## 📈 性能影响

| Timeout 值 | 影响 |
|----------|------|
| 很小 (1-5s) | ⚠️ 容易误杀慢速命令 |
| 中等 (10-60s) | ✓ 推荐用于大多数开发任务 |
| 很大 (>300s) | ⚠️ LLM 可能长时间等待 |
| 默认值 (100s) | ✓ 生产环境推荐值 |

---

## 🔍 代码流程图

```
start
  │
  ├─ command 为空? ─── YES ─→ 返回 "ERROR: Shell command cannot be empty."
  │                         
  NO
  │
  ├─ subprocess.run(timeout=timeout)
  │
  ├─ 执行成功? ─── YES ─→ 正常返回 (SUCCESS 或 ERROR)
  │                      
  NO (超时)
  │
  └─ TimeoutExpired 异常
      │
      ├─ 提取部分输出 (e.stdout, e.stderr)
      ├─ 截断输出 (MAX_OUTPUT_LENGTH)
      └─ 返回 TIMEOUT_ERROR 状态 (returncode=-1)
```

---

## ✅ 总结

**ShellTool 的 timeout 处理:**

1. **参数**: 可选的 `timeout` 整数参数，默认 100 秒
2. **执行**: 传递给 `subprocess.run()` 的 `timeout` 参数
3. **超时处理**: 
   - 进程被强制终止
   - 部分输出被保存
   - 返回 `TIMEOUT_ERROR` 状态和 `returncode=-1`
4. **安全性**: 防止 LLM 被长时间运行的命令阻塞
5. **可观测性**: 即使超时也能看到执行进度
