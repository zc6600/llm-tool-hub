# src/llm_tool_hub/filesystem_tool/base_filesystem_tool.py

import logging
from typing import Union
from pathlib import Path
from ..base_tool import BaseTool

logger = logging.getLogger(__name__)

# 定义上下文窗口大小 (所有需要同步的工具共享此常量)
CONTEXT_WINDOW_SIZE = 5

class BaseFileSystemTool(BaseTool):
    """
    A base class for all file system tools (Read, Create, Modify).
    它封装了路径安全性、根路径初始化，并提供了通用的文件内容操作辅助方法。
    """
    
    root_path: Path
    unsafe_mode: bool
    
    def __init__(self, root_path: Union[str, Path] = None, unsafe_mode: bool = False):
        """Initializes the file system tool with the project root and safety mode."""
        super().__init__()

        if root_path is None:
            self.root_path = Path.cwd().resolve()
        else:
            self.root_path = Path(root_path).resolve()

        # Look Before You Leap (LBYL): Check if root_path is a valid directory
        if not self.root_path.is_dir():
            raise ValueError(f"Root path must be a valid directory: {self.root_path}")
        
        self.unsafe_mode = unsafe_mode

        if self.unsafe_mode:
            logger.warning(f"{self.__class__.__name__} initialized in UNSAFE MODE.")

        logger.debug(f"{self.__class__.__name__} initialized with secure root: {self.root_path}")


    def _check_path_safety(self, file_path: str, must_exist: bool = None, allow_dir: bool = False) -> Path:
        """
        Validates the file path to prevent path traversal and ensures it's within the root.
        
        ... (implementation of _check_path_safety remains the same) ...
        """
        if not file_path:
            raise ValueError("File path is empty, please check your path configuration.")

        input_path = Path(file_path)
        target_path = (self.root_path / input_path).resolve()

        # Path Traversal Check (Must be inside root)
        if not self.unsafe_mode:
            try:
                target_path.relative_to(self.root_path)
            except ValueError:
                raise ValueError(
                    f"Access Denied: File path '{file_path}' must be inside the configured root: {self.root_path}"
                )
        
        # --- Existence and Type Checks ---
        
        target_exists = target_path.exists()

        # Check 1: Existence requirement
        if must_exist is True and not target_exists:
            raise FileNotFoundError(f"File not found at path: {file_path}")
        
        # Check 2: Creation restriction (Only for tools that should not overwrite)
        if must_exist is False and target_exists:
            raise ValueError(f"File already exists at path: {file_path}. Cannot overwrite.")

        # Check 3: Directory check
        if target_exists and target_path.is_dir():
            if not allow_dir:
                raise ValueError(f"Path is a directory: {file_path}. Operation requires a file path.")
        
        # Check 4: Parent directory for creation (If file doesn't exist yet)
        if not target_exists and not target_path.parent.is_dir():
            raise FileNotFoundError(f"Parent directory does not exist for path: {file_path}")
        
        return target_path

    # --- NEW: Shared Utility Methods for File Content ---
    
    def _get_lines(self, target_path: Path) -> list[str]:
        """Reads the entire file into a list of lines (without trailing newlines)."""
        try:
            with open(target_path, 'r', encoding='utf-8') as f:
                # Read all lines and strip the trailing newline character
                return [line.rstrip('\n') for line in f.readlines()]
        except Exception as e:
            raise IOError(f"Failed to read file contents: {e}")

    def _write_file_content(self, target_path: Path, modified_lines: list[str]):
        """Helper to write the modified lines back to the file."""
        new_content_to_write = '\n'.join(modified_lines)
        
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(new_content_to_write)
            
    def _format_modified_content(self, target_path: Path, new_total_lines: int, modified_start_line: int, new_lines_count: int) -> str:
        """
        Reads the modified file and formats a synchronized content window 
        around the change for the LLM to update its state.
        
        :param modified_start_line: The 1-indexed start line of the *new* content block.
        :param new_lines_count: The number of lines in the *new* content block.
        """
        formatted_content_lines = []
        
        # Calculate the 1-indexed range to read (including context)
        read_start_line = max(1, modified_start_line - CONTEXT_WINDOW_SIZE)
        
        # New end line is modified_start_line + new_lines_count - 1
        window_end_line = modified_start_line + new_lines_count - 1
        
        # read_end_line includes the context after the change
        # +1 is for the inclusive loop logic (read up to and including this line number)
        read_end_line = min(new_total_lines, window_end_line + CONTEXT_WINDOW_SIZE + 1) 

        try:
            with open(target_path, 'r', encoding='utf-8') as f:
                # Read only the lines within the window for token efficiency
                for line_number, line in enumerate(f, 1):
                    if line_number < read_start_line:
                        continue
                    if line_number > read_end_line:
                        break
                        
                    line_content = line.rstrip('\n')
                    formatted_content_lines.append(f"{line_number}:{line_content}")
            
            read_content_string = "\n".join(formatted_content_lines)
            
            # --- Generate Synchronized Message ---
            
            prefix = "[...]\n" if read_start_line > 1 else ""
            suffix = "\n[...]" if read_end_line <= new_total_lines and read_end_line < new_total_lines else "" # Only show suffix if truncation happened
            
            # Fix: If read_end_line equals new_total_lines, it means we read to the end.
            if read_end_line == new_total_lines and not (new_total_lines == modified_start_line + new_lines_count - 1 + CONTEXT_WINDOW_SIZE + 1) :
                 suffix = "" # No suffix if we reached the end
            
            return (
                f"[SYNCHRONIZED CONTENT WINDOW - Lines {read_start_line} to {read_end_line}]:\n"
                "-------------------------------------------------------------------------- \n"
                f"{prefix}{read_content_string}{suffix}\n"
                "-------------------------------------------------------------------------- \n"
                f"NOTE: Total lines in file now: {new_total_lines}. All subsequent operations must use these new line numbers."
            )
            
        except Exception as e:
            logger.warning(f"Modification succeeded, but failed to read back content for synchronization: {e}")
            return f"\nWARNING: Modification succeeded, but failed to synchronize file content due to an internal read error: {e}"