import pytest
import platform
from pathlib import Path
import re
import time
from llm_tool_hub.shell_tool.shell_tool import ShellTool, MAX_OUTPUT_LENGTH, DEFAULT_TIMEOUT

# --- Fixtures and Setup ---

@pytest.fixture
def shell_tool(tmp_path: Path) -> ShellTool:
    """Fixture to initialize ShellTool with a temporary root path."""
    return ShellTool(root_path=tmp_path)

@pytest.fixture(autouse=True)
def setup_test_files(tmp_path: Path):
    """Setup files needed for command testing within the root_path."""
    (tmp_path / "hello.txt").write_text("Hello World\n")
    (tmp_path / "test_dir").mkdir()
    (tmp_path / "test_dir" / "inner_file.py").write_text("print('inner')\n")


# --- Helper for parsing structured output ---

def parse_result(result: str) -> dict:
    """Parses the structured output of the ShellTool."""
    data = {}
    
    # Simple regex to find the main fields
    data['STATUS'] = re.search(r"STATUS: (.+)", result).group(1).strip()
    data['RETURN_CODE'] = int(re.search(r"RETURN_CODE: (-?\d+)", result).group(1))
    
    # Extract STDOUT and STDERR sections
    stdout_match = re.search(r"--- STDOUT ---\n(.*?)\n--- STDERR ---", result, re.DOTALL)
    stderr_match = re.search(r"--- STDERR ---\n(.*?)\n----------------------------", result, re.DOTALL)
    
    data['STDOUT'] = stdout_match.group(1).strip() if stdout_match else ""
    data['STDERR'] = stderr_match.group(1).strip() if stderr_match else ""
    
    # Check for WARNING
    data['WARNING'] = re.search(r"WARNING: (.+)", result)
    data['WARNING'] = data['WARNING'].group(1).strip() if data['WARNING'] else None
    
    return data

# ==============================================================================
# A. Success Cases (Return Code 0)
# ==============================================================================

def test_successful_command_ls(shell_tool: ShellTool):
    """A.1: Tests a basic successful command (ls/dir)."""
    command = "ls -F" if platform.system() != "Windows" else "dir /B"
    result_str = shell_tool.run(command=command)
    result = parse_result(result_str)
    
    assert result['STATUS'] == "SUCCESS"
    assert result['RETURN_CODE'] == 0
    
    # Check for the setup files/directories in the output
    assert "hello.txt" in result['STDOUT']
    assert ("test_dir/" if platform.system() != "Windows" else "test_dir") in result['STDOUT']
    assert result['STDERR'] == ""
    assert result['WARNING'] is None
    

def test_successful_command_grep(shell_tool: ShellTool):
    """A.2: Tests a command with specific stdout."""
    command = "grep 'World' hello.txt"
    result_str = shell_tool.run(command=command)
    result = parse_result(result_str)
    
    assert result['STATUS'] == "SUCCESS"
    assert result['RETURN_CODE'] == 0
    assert "Hello World" in result['STDOUT']
    assert result['STDERR'] == ""


def test_command_with_expected_stdout_and_stderr(shell_tool: ShellTool):
    """A.3: Tests a command that writes to both stdout and stderr (simulated)."""
    # Use 'echo' to write to stdout and 'cat' on a non-existent file to write to stderr
    # Windows equivalent is complex, so we skip for Windows for simplicity or use 'cmd /c'
    if platform.system() != "Windows":
        command = "echo 'stdout message' && cat non_existent_file.txt"
        
        result_str = shell_tool.run(command=command)
        result = parse_result(result_str)
        
        # NOTE: Because 'cat non_existent_file.txt' fails, the RETURN_CODE will be non-zero (ERROR)
        assert result['STATUS'] == "ERROR"
        assert result['RETURN_CODE'] != 0
        assert "stdout message" in result['STDOUT']
        assert "No such file or directory" in result['STDERR'] or "cannot open" in result['STDERR']

# ==============================================================================
# B. Failure Cases (Non-Zero Return Code)
# ==============================================================================

def test_command_with_non_zero_return_code(shell_tool: ShellTool):
    """B.1: Tests a command that fails (non-zero return code)."""
    command = "false" if platform.system() != "Windows" else "cmd /c exit 1"
    result_str = shell_tool.run(command=command)
    result = parse_result(result_str)
    
    assert result['STATUS'] == "ERROR"
    assert result['RETURN_CODE'] != 0 # Should be 1 typically
    assert result['STDOUT'] == ""
    assert result['WARNING'] is None


def test_command_not_found(shell_tool: ShellTool):
    """B.2: Tests a command that does not exist."""
    command = "nonexistent_binary_xyz"
    result_str = shell_tool.run(command=command)
    result = parse_result(result_str)
    
    # Command not found is usually a non-zero exit code, and error written to STDERR
    assert result['STATUS'] == "ERROR"
    assert result['RETURN_CODE'] != 0
    assert "command not found" in result['STDERR'] or "is not recognized" in result['STDERR']
    

# ==============================================================================
# C. Safety and Limit Cases (Timeout and Truncation)
# ==============================================================================

def test_command_timeout(shell_tool: ShellTool):
    """C.1: Tests a command that exceeds the timeout, verifying partial output capture."""
    # Command to sleep for 3 seconds, but we set timeout to 1 second.
    command = "sleep 3" if platform.system() != "Windows" else "timeout 3"
    
    # We execute a command that produces some output before the sleep 
    # to test partial output capture, if possible.
    if platform.system() != "Windows":
        command = "echo 'Starting...' && sleep 3"
    else:
        # Windows timeout command is tricky to capture partial output cleanly
        command = "echo Starting && ping -n 4 127.0.0.1 >nul" # ping takes ~3s
        
    result_str = shell_tool.run(command=command, timeout=1) # 1 second timeout

    result = parse_result(result_str)

    assert result['STATUS'] == "TIMEOUT_ERROR"
    assert result['RETURN_CODE'] == -1
    
    # Check that the error message indicates timeout and partial output
    assert "Command timed out after 1s" in result['WARNING']
    
    # Assert that at least some sign of execution or partial output exists
    # Note: Testing for *exact* partial output is highly platform-dependent, 
    # so we check for the status/error message structure.
    if platform.system() != "Windows":
        # Check if the 'Starting...' was captured before the timeout
        assert 'Starting...' in result['STDOUT'] or 'No partial stdout captured' in result['STDOUT']
        
    assert result['STDERR'] == "No partial stderr captured."


def test_command_truncation(shell_tool: ShellTool):
    """C.2: Tests output truncation when output exceeds MAX_OUTPUT_LENGTH."""
    # Create a command that generates output slightly more than the limit (e.g., limit + 100)
    # We use 'yes' or a loop to generate a long string.
    
    # In a real environment, MAX_OUTPUT_LENGTH is 5000. We'll simulate a 10000 char output.
    long_string_length = MAX_OUTPUT_LENGTH + 100
    
    if platform.system() != "Windows":
        # Use a shell function to repeat a character (easier than 'yes' for exact length)
        # Repeats 'a' N times
        command = f"python3 -c \"print('a' * {long_string_length})\""
    else:
        # Windows: Use a loop to print many times
        command = f"powershell -command \"'a' * {long_string_length}\""
        
    result_str = shell_tool.run(command=command)
    result = parse_result(result_str)
    
    assert result['STATUS'] == "SUCCESS"
    assert result['RETURN_CODE'] == 0
    
    # Check for truncation message at the end of STDOUT
    assert result['STDOUT'].endswith("[OUTPUT TRUNCATED]")
    
    # Check that the WARNING field is populated
    assert "Output truncated after" in result['WARNING']
    
    # Check that the length is correct (MAX_OUTPUT_LENGTH chars + truncation marker)
    # The truncation marker is "\n[OUTPUT TRUNCATED]" (20 chars + 1 newline)
    expected_length_check = MAX_OUTPUT_LENGTH + 20
    # Since we are checking the parsed and stripped content, we check the length of the string
    # without the final "\n[OUTPUT TRUNCATED]"
    assert len(result['STDOUT']) <= MAX_OUTPUT_LENGTH + 20 # Should be very close to the limit + marker length
    
# ==============================================================================
# D. Edge Cases
# ==============================================================================

def test_command_empty_input(shell_tool: ShellTool):
    """D.1: Tests empty command input."""
    result_str = shell_tool.run(command="")
    assert result_str == "ERROR: Shell command cannot be empty."

def test_command_no_stdout_only_stderr(shell_tool: ShellTool):
    """D.2: Tests a command with no stdout, only stderr."""
    # Try to execute a command that will fail with a clean stderr message
    command = "cat non_existent_file_xyz.txt" if platform.system() != "Windows" else "type non_existent_file_xyz.txt"
    
    result_str = shell_tool.run(command=command)
    result = parse_result(result_str)
    
    assert result['STATUS'] == "ERROR"
    assert result['RETURN_CODE'] != 0
    assert result['STDOUT'] == ""
    assert "non_existent_file_xyz.txt" in result['STDERR']

def test_command_no_output(shell_tool: ShellTool):
    """D.3: Tests a command that produces no output (e.g., touch)."""
    command = "touch new_file.txt" if platform.system() != "Windows" else "echo. > new_file.txt"
    result_str = shell_tool.run(command=command)
    result = parse_result(result_str)

    assert result['STATUS'] == "SUCCESS"
    assert result['RETURN_CODE'] == 0
    assert result['STDOUT'] == ""
    assert result['STDERR'] == ""
    
    # Verify the file was created in the root_path
    assert (shell_tool.root_path / "new_file.txt").exists()