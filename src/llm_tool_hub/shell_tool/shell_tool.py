# src/llm_tool_hub/shell_tool/shell_tool.py

import subprocess
import logging
import os
from typing import Dict, Any, Union
from pathlib import Path
from ..base_tool import BaseTool # Assuming BaseTool is the general base class

__all__ = ['ShellTool', 'int']

logger = logging.getLogger(__name__)

# --- Constants ---
MAX_OUTPUT_LENGTH = 5000
DEFAULT_TIMEOUT = 100 

# --- Helper Function: Output Truncation ---
def _truncate_output(output: str) -> tuple[str, str]:
    """Truncates output string and returns a warning if truncation occurred."""
    warning = ""
    if len(output) > MAX_OUTPUT_LENGTH:
        output = output[:MAX_OUTPUT_LENGTH] + "\n[OUTPUT TRUNCATED]"
        warning = f"Output truncated after {MAX_OUTPUT_LENGTH} characters."
    return output, warning

# --- Shell Tool Class ---
class ShellTool(BaseTool):
    """
    A tool to execute shell commands and return structured results.
    It runs from the project root and includes security features like timeouts and output truncation.
    """
    
    # --- 1. Required Metadata ---
    name: str = "shell_tool"
    description: str = (
        "**[DANGEROUS: OS INTERACTION]** Executes a shell command (e.g., 'ls -l', 'git status', 'pip install') "
        "and returns the standard output (stdout), standard error (stderr), and return code in a structured format. "
        "The operation runs from the project root directory. Use the 'timeout' parameter for long-running commands. "
        "IMPORTANT: For long-running commands like 'pip install', 'git clone', 'npm install', or machine learning training, "
        "ALWAYS increase the 'timeout' parameter (e.g., timeout=120 for 2 minutes or timeout=300 for 5 minutes) to avoid timeout errors. "
        f"Default timeout is {DEFAULT_TIMEOUT} seconds. "
        f"Output is truncated to {MAX_OUTPUT_LENGTH} characters for safety."
    )
    
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The full shell command string to execute. Example: 'ls -aF src/'",
            },
            "timeout": {
                "type": "integer",
                "description": f"Optional: Max time in seconds to wait for the command to complete. Defaults to {DEFAULT_TIMEOUT}.",
                "default": DEFAULT_TIMEOUT,
                "minimum": 1
            }
        },
        "required": ["command"]
    }

# Add attribute definitions for clarity and access
    root_path: Path
    
    def __init__(self, root_path: Union[str, Path] = None, unsafe_mode: bool = False):
        """Initializes the shell tool with the execution root path."""
        super().__init__()
        
        # We explicitly define and resolve the root path
        if root_path is None:
            self.root_path = Path.cwd().resolve()
        else:
            self.root_path = Path(root_path).resolve()
            
        # Ensure the root path is a directory, similar to BaseFileSystemTool
        if not self.root_path.is_dir():
            # This should generally not happen with pytest's tmp_path, but is good safety
            raise ValueError(f"Root path must be a valid directory: {self.root_path}")

        # Note: unsafe_mode can be handled here if needed, but we'll focus on root_path
        
        logger.debug(f"{self.__class__.__name__} initialized with secure root: {self.root_path}")
    def _format_result(self, 
                       command: str, 
                       status: str, 
                       returncode: int, 
                       stdout: str, 
                       stderr: str, 
                       warning: str = "") -> str:
        """Formats the final structured output string for the LLM."""
        
        # Safely get root_path for display
        working_dir = getattr(self, 'root_path', Path.cwd())
        
        # We build the result line by line, conditionally adding the WARNING line.
        result = (
            f"--- SHELL COMMAND RESULT ---\n"
            f"STATUS: {status}\n"
            f"COMMAND: {command}\n"
            f"RETURN_CODE: {returncode}\n"
            f"WORKING_DIR: {working_dir}\n"
        )
        
        # Conditionally add the WARNING line
        if warning:
            # Note: We ensure there are no backslashes inside the f-string's braces.
            result += f"WARNING: {warning.strip()}\n"
        
        result += (
            f"--- STDOUT ---\n{stdout.strip()}\n"
            f"--- STDERR ---\n{stderr.strip()}\n"
            f"----------------------------"
        )
        
        return result
    def run(self, command: str, timeout: int = DEFAULT_TIMEOUT) -> str:
        """
        Executes the shell command with safety limits (timeout, truncation)
        and returns a structured result.
        """
        if not command:
            return "ERROR: Shell command cannot be empty."

        # Use device encoding or default to utf-8 for robustness
        encoding = os.device_encoding(1) or os.getenv('PYTHONIOENCODING') or 'utf-8'
        
        try:
            # Execute the command
            process = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                check=False, # We handle the return code ourselves
                text=True, 
                timeout=timeout,
                cwd=getattr(self, 'root_path', None), # Use self.root_path if available
                encoding=encoding,
                errors='replace', # Replace undecodable chars
            )

            # Success or Non-Timeout Error Path
            
            # Truncate output and gather warnings
            stdout_truncated, stdout_warning = _truncate_output(process.stdout)
            stderr_truncated, stderr_warning = _truncate_output(process.stderr)
            
            status = "SUCCESS" if process.returncode == 0 else "ERROR"
            warning = stdout_warning + (" " + stderr_warning if stderr_warning else "")

            # Format and return the result
            return self._format_result(
                command=command,
                status=status,
                returncode=process.returncode,
                stdout=stdout_truncated,
                stderr=stderr_truncated,
                warning=warning
            )

        except subprocess.TimeoutExpired as e:
            # --- Timeout Handling: Capture Partial Output ---
            
            # Extract partial stdout and stderr from the exception object
            partial_stdout = e.stdout if e.stdout else "No partial stdout captured."
            partial_stderr = e.stderr if e.stderr else "No partial stderr captured."
            
            # Truncate partial output
            stdout_truncated, stdout_warning = _truncate_output(partial_stdout)
            stderr_truncated, stderr_warning = _truncate_output(partial_stderr)
            
            warning = stdout_warning + (" " + stderr_warning if stderr_warning else "")

            # Format the timeout error message
            return self._format_result(
                command=command,
                status="TIMEOUT_ERROR",
                returncode=-1, # -1 for internal timeout error
                stdout=stdout_truncated,
                stderr=stderr_truncated,
                warning=f"Command timed out after {timeout}s. Partial output captured. {warning}"
            )

        except Exception as e:
            # Catch other unexpected system errors
            return self._format_result(
                command=command,
                status="FATAL_ERROR",
                returncode=-2, # -2 for other fatal internal errors
                stdout="",
                stderr=f"An unexpected Python error occurred: {type(e).__name__}: {str(e)}",
                warning=""
            )