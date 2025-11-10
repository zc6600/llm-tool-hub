# ShellTool Timeout 处理总结

## 快速概览

ShellTool 通过 `subprocess.run()` 的 `timeout` 参数实现对命令执行时间的控制。

---

## Timeout 参数

```python
"timeout": {
    "type": "integer",           # 整数类型，单位：秒
    "default": 100,              # 默认值：100 秒
    "minimum": 1,                # 最小值：1 秒
    "description": "Max time in seconds to wait for the command"
}
```

---

## 三种执行结果

### 1. ✅ 正常完成 (无超时)

```python
# 调用
shell_tool.run(command="echo hello", timeout=100)

# 结果
STATUS: SUCCESS          # 或 ERROR（取决于 exit code）
RETURN_CODE: 0           # 命令的 exit code
STDOUT: hello
STDERR: (可能为空)
```

### 2. ⏱️ 命令超时 (超过 timeout)

```python
# 调用
shell_tool.run(command="sleep 300", timeout=5)

# 5 秒后，进程被强制终止

# 结果
STATUS: TIMEOUT_ERROR
RETURN_CODE: -1                    # 特殊值表示超时
STDOUT: (部分输出，如果有的话)
WARNING: Command timed out after 5s. Partial output captured.
```

### 3. ⚠️ 系统异常

```python
# 调用
shell_tool.run(command="invalid_command", timeout=10)

# 结果
STATUS: FATAL_ERROR
RETURN_CODE: -2                    # 特殊值表示系统错误
STDERR: An unexpected Python error occurred: ...
```

---

## 处理流程图

```
┌─────────────────────────────────┐
│ subprocess.run(                 │
│   command="...",                │
│   timeout=timeout,              │
│   shell=True,                   │
│   capture_output=True           │
│ )                               │
└──────────────┬──────────────────┘
               │
        ┌──────┴──────┐
        │             │
    完成     超时
    (0s-     (>timeout)
     timeout)
    │             │
    ▼             ▼
正常处理    抛出异常
    │      TimeoutExpired
    │             │
    │        ┌────┴────┐
    │        │          │
    │    提取e.stdout  提取e.stderr
    │        │          │
    │        └────┬─────┘
    │             │
    │        返回部分输出
    │             │
    └─────┬───────┘
          │
          ▼
    ┌──────────────┐
    │ _format_result
    │ 格式化返回   │
    └──────────────┘
```

---

## 代码实现细节

### subprocess.run() 调用

```python
process = subprocess.run(
    command,
    shell=True,
    capture_output=True,
    timeout=timeout,              # ← 这里设置超时
    cwd=self.root_path,           # 在指定目录执行
    encoding='utf-8',
    errors='replace',             # 编码错误时替换
    check=False,                  # 不抛出异常，自己处理 returncode
)
```

### 超时异常处理

```python
except subprocess.TimeoutExpired as e:
    # 进程已被强制终止
    
    partial_stdout = e.stdout or "No partial stdout captured."
    partial_stderr = e.stderr or "No partial stderr captured."
    
    # 仍然可以获取部分输出
    return self._format_result(
        status="TIMEOUT_ERROR",
        returncode=-1,            # 特殊的负值
        stdout=partial_stdout,    # 部分输出
        stderr=partial_stderr,    # 部分错误信息
        warning=f"Command timed out after {timeout}s"
    )
```

---

## 返回值对照

| 情况 | STATUS | RETURN_CODE | 说明 |
|------|--------|-------------|------|
| 成功 | SUCCESS | 0 | 命令正常完成 |
| 失败 | ERROR | >0 | 命令出错 |
| 超时 | TIMEOUT_ERROR | -1 | 超过 timeout 时限 |
| 异常 | FATAL_ERROR | -2 | Python 执行异常 |

---

## LLM 使用建议

### 设置合理的超时值

```python
# 快速命令
shell_tool.run(command="ls -la", timeout=5)

# 网络操作
shell_tool.run(command="git clone ...", timeout=30)

# 数据处理
shell_tool.run(command="python script.py", timeout=300)  # 5 分钟

# 默认值（推荐）
shell_tool.run(command="echo hello")  # 使用默认 100 秒
```

### 处理超时响应

```python
# 检查是否超时
if "TIMEOUT_ERROR" in response:
    # 方案 1: 增加超时时间重试
    # 方案 2: 分解任务为多个小任务
    # 方案 3: 告诉用户任务太长
```

---

## 关键特性

✅ **进程强制终止** - 不会让 LLM 无限等待
✅ **部分输出保留** - 可以看到执行进度
✅ **清晰的错误状态** - 通过 RETURN_CODE 区分各种情况
✅ **输出安全** - 超大输出会被截断（MAX_OUTPUT_LENGTH）

