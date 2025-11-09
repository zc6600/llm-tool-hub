# tests/filesystem_tool/test_read_file.py

import os
import pytest
import logging
import tempfile
from pathlib import Path

from llm_tool_hub.filesystem_tool.read_file_tool import ReadFileTool

MAX_LINE_CHARS = 5000
# ----------------------------------
# Tests Read File Tool
# 1. Path Traversal Denial
# 2. Basic Reading Function
# 3. Line-based Chunking
# 4. 
# ----------------------------------

MULTI_LINE_CONTENT = "Line 1: Hello\nLine 2: World\nLine 3: Test\nLine 4: End"

@pytest.fixture
def create_test_file(tmp_path: Path):
    """Fixture to create a standard multi-line file in the root path. """
    test_file = tmp_path / "data.txt"
    test_file.write_text(MULTI_LINE_CONTENT, encoding='utf-8')
    return test_file

# --- Scenario A: Security and Access Denial Tests ---

def test_read_file_path_traversal_denied(tmp_path: Path):
    """A.1: Verifies that the tool denies path traversal attacks in secure mode."""
    # 1. Setup: Create an external file outside the sandbox (tmp_path)
    external_dir = tmp_path.parent
    external_file = external_dir / "external_secret.txt"
    external_file.write_text("Secret Data Outside Sandbox", encoding='utf-8')

    # 2. Construct malicious path (e.g., ../external_secret.txt)
    malicious_path = os.path.join("..", external_file.name)

    # 3. Initialize tool (default secure mode)
    tool = ReadFileTool(root_path=tmp_path, unsafe_mode=False)

    # 4. Execution
    result = tool.run(file_path=malicious_path)

    assert result.startswith("ERROR:") or result.startswith("Error:")
    assert "Access Denied" in result
    assert str(tmp_path) in result 
    external_file.unlink()

def test_read_file_path_traversal_allowed_in_unsafe_mode(tmp_path: Path, caplog: pytest.LogCaptureFixture):
    """A.2: Verifies that path traversal is allowed when unsafe_mode=True."""
    # 1. Setup: Create an external file
    external_dir = tmp_path.parent
    external_file = external_dir / "external_secret_unsafe.txt"
    external_content = "This should only be readable in unsafe mode."
    external_file.write_text(external_content, encoding='utf-8')
    malicious_path = os.path.join("..", external_file.name) 
    
    # 2. Initialize tool (UNSAFE MODE enabled)
    with caplog.at_level(logging.WARNING):
        tool = ReadFileTool(root_path=tmp_path, unsafe_mode=True) 
    
    # 3. Execution
    result = tool.run(file_path=malicious_path) 
    
    # 4. Verification: Expected to read successfully
    assert result.startswith(f"SUCCESS:")
    assert external_content in result
    
    # 5. Verification: Check for WARNING log
    assert "ReadFileTool initialized in UNSAFE MODE" in caplog.text
    external_file.unlink()

def test_read_file_absolute_path_denied(tmp_path: Path):
    """A.3: Verifies that absolute paths outside the root are denied in secure mode."""
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as tf:
        external_abs_path = Path(tf.name)
        tf.write("Absolute Secret")
    
    tool = ReadFileTool(root_path=tmp_path, unsafe_mode=False) 
    result = tool.run(file_path=str(external_abs_path)) 
    
    assert result.startswith("ERROR:") or result.startswith("Error:")
    assert "Access Denied" in result
    external_abs_path.unlink()

# --- Scenario B: Basic Functionality and Failure Modes ---
def test_read_file_basic_success(tmp_path: Path, create_test_file: Path):
    """B.1: Verifies basic successful file reading."""
    tool = ReadFileTool(root_path=tmp_path) 
    result = tool.run(file_path="data.txt") 
    
    assert result.startswith("SUCCESS: Chunk of 'data.txt' (Lines 1-4)")
    expected_content = (
        "1:Line 1: Hello\n"
        "2:Line 2: World\n"
        "3:Line 3: Test\n"
        "4:Line 4: End"
    )
    assert expected_content in result

def test_read_file_empty_file(tmp_path: Path):
    """B.2: Verifies reading an empty file."""
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("", encoding='utf-8')
    tool = ReadFileTool(root_path=tmp_path)
    result = tool.run(file_path="empty.txt")
    
    # Expected to return Lines 1-0 for an empty file
    assert result.startswith("SUCCESS: Chunk of 'empty.txt' (Lines 1-0)")
    assert "is empty" in result

def test_read_file_not_found(tmp_path: Path):
    """B.3: Attempts to read a non-existent file."""
    tool = ReadFileTool(root_path=tmp_path) 
    result = tool.run(file_path="non_existent_file.txt") 
    
    assert result.startswith("ERROR:")
    assert "File not found at path:" in result

def test_read_file_is_directory(tmp_path: Path):
    """B.4: Attempts to read a directory (tmp_path itself)."""
    tool = ReadFileTool(root_path=tmp_path) 
    result = tool.run(file_path=".") 
    
    assert result.startswith("ERROR:")
    assert "Path is a directory:" in result
    assert "Operation requires a file path" in result

def test_read_file_empty_path(tmp_path: Path):
    """B.5: Attempts to provide an empty file path."""
    tool = ReadFileTool(root_path=tmp_path) 
    result = tool.run(file_path="") 
    
    assert result.startswith("ERROR:")
    assert "File path is empty" in result

# --- Scenario C: Precise Chunking and Limits Tests ---

def test_read_file_line_chunking(tmp_path: Path, create_test_file: Path):
    """C.1: Verifies precise chunking using start_line and end_line."""
    tool = ReadFileTool(root_path=tmp_path) 
    
    # Read starting from line 2
    result_start = tool.run(file_path="data.txt", start_line=2)
    assert result_start.startswith("SUCCESS: Chunk of 'data.txt' (Lines 2-4)")
    assert "Line 1" not in result_start
    assert "Line 2: World" in result_start
    
    # Read lines 2 and 3 (end_line=4 is exclusive)
    result_chunk = tool.run(file_path="data.txt", start_line=2, end_line=4)
    assert result_chunk.startswith("SUCCESS: Chunk of 'data.txt' (Lines 2-3)")
    assert "Line 1" not in result_chunk
    assert "Line 4" not in result_chunk
    assert "Line 2: World" in result_chunk
    assert "Line 3: Test" in result_chunk

def test_read_file_invalid_line_range(tmp_path: Path, create_test_file: Path):
    """C.2: Verifies invalid line range input (end_line <= start_line)."""
    tool = ReadFileTool(root_path=tmp_path) 
    result_invalid = tool.run(file_path="data.txt", start_line=5, end_line=3)
    assert result_invalid == "ERROR: end_line must be greater than start_line." # Note: Corrected expected string to use ERROR:

def test_read_file_line_char_truncation_check(tmp_path: Path):
    """C.3: Verifies that the single-line character limit (MAX_LINE_CHARS) is applied."""
    # Create a single line file that is slightly longer than the limit
    # We create a line longer than MAX_LINE_CHARS
    long_content = "B" * (MAX_LINE_CHARS + 100) + "\n"
    test_file = tmp_path / "long_line.txt"
    test_file.write_text(long_content, encoding='utf-8')
    
    tool = ReadFileTool(root_path=tmp_path)
    result = tool.run(file_path="long_line.txt")
    
    # Verify warning message appears
    expected_warning = f"[WARNING: Line 1 was truncated to {MAX_LINE_CHARS} characters]"
    assert expected_warning in result
    
    # Verify content length (Check that the returned content is NOT the full original content)
    # The actual content length should be close to MAX_LINE_CHARS + length of the warning line
    long_content_truncated = "B" * MAX_LINE_CHARS
    
    # Find the line that was the content
    content_line_with_warning = [
        line for line in result.split('\n') 
        if line.startswith('1:') and expected_warning in line
    ][0]
    # Verify the line was truncated to the limit
    assert f"1:{long_content_truncated}" in content_line_with_warning

# --- Scenario D: Accurate Error Reporting Tests ---

def test_read_file_high_start_line_error(tmp_path: Path, create_test_file: Path):
    """D.1: Verifies accurate error message when start_line exceeds total lines."""
    tool = ReadFileTool(root_path=tmp_path) 
    
    # File has 4 lines, request to start at line 100
    result = tool.run(file_path="data.txt", start_line=100)
    
    assert result.startswith("ERROR:")
    assert "Requested start_line (100) is greater than the total lines in file (4)." in result

# --- Scenario E: to_callable and Function Calling Tests ---
def test_read_file_to_callable_metadata():
    """F.1: Verifies that to_callable returns a callable function with correct metadata attributes attached."""
    
    tool = ReadFileTool(root_path=Path.cwd())
    callable_tool_func = tool.to_callable()
    
    # 1. Check if the result is a function/callable object
    assert callable(callable_tool_func)
    
    # 2. Check that the name and docstring were set dynamically
    assert callable_tool_func.__name__ == tool.name
    assert callable_tool_func.__doc__ == tool.description
    
    # 3. Check for the dynamically attached JSON schema attribute
    # Note: Accessing using getattr is safer than direct attribute access
    json_schema = getattr(callable_tool_func, 'json_schema', None)
    
    assert json_schema is not None
    assert json_schema == tool.parameters
    assert json_schema["required"] == ["file_path"]


def test_read_file_execution_via_to_callable(tmp_path: Path, create_test_file: Path):
    """F.2: Verifies the tool can be executed successfully when called via the to_callable wrapper."""
    
    tool = ReadFileTool(root_path=tmp_path)
    
    # The to_callable function object itself is the wrapper we execute
    tool_func_wrapper = tool.to_callable()
    
    # Simulate a function call from the framework, passing kwargs
    args = {
        "file_path": "data.txt",
        "start_line": 2,
        "end_line": 4 # Should read lines 2 and 3
    }
    
    # Execute the wrapped function
    result = tool_func_wrapper(**args)
    
    # Verification (Should match the successful chunking test C.1)
    assert result.startswith("SUCCESS: Chunk of 'data.txt' (Lines 2-3)")
    assert "Line 2: World" in result
    assert "Line 1" not in result
    assert "Line 4" not in result