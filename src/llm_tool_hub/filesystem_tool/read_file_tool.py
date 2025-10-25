# src/llm_tool_hub/filesystem_tool/read_file_tool.py

import logging
from typing import Dict, Any, Union
from pathlib import Path
from ..base_tool import BaseTool

logger = logging.getLogger(__name__)
MAX_LINE_CHARS = 5000
class ReadFileTool(BaseTool):
    """
    A tool to safely read the content of a text file from the project's working directory.

    This tool supports line-based chunking
    """

    # --- 1. Required Metadata ---
    name: str = "read_file"
    description: str = (
        "A tool to reads the content of a text file"
        "Supports line-based reading (start_line/end_line) for large files"
    )

    # JSON Schema for the 'run' method parameters

    parameters: Dict[str, Any] = {
        "type": "object",
        "properties" : {
            "file_path": {
                "type": "string",
                "description": (
                    "The relative path to the target file from the root_path. "
                    "Example: 'data/input.txt'"
                ),
            },
            "start_line": {
                "type": "integer",
                "description": (
                    "The line number to start reading from (1-indexed). "
                    "Defaults to 1 (beginning of file)."
                ),
                "default": 1,
            },
            "end_line": {
                "type": ["integer", "null"],
                "description": (
                    "The line number to stop reading before (exclusive). "
                    "If not provided, reads until the end of the file."
                ),
                "default": None,
            }
        },
        "required": ["file_path"]
    }

    root_path: Path
    unsafe_mode: bool
    def __init__(self, root_path: Union[str, Path] = None, unsafe_mode: bool = False):
        super().__init__()

        if root_path is None:
            self.root_path = Path.cwd().resolve()
        else:
            self.root_path = Path(root_path).resolve()

        # LBYL
        if not self.root_path.is_dir():
            raise ValueError(f"Root path must be a valid directory: {self.root_path}")
        
        self.unsafe_mode = unsafe_mode

        if self.unsafe_mode:
            logger.warning("ReadFileTool initialized in UNSAFE MODE. LLM agent can edit all files on your system")

        logger.debug(f"ReadFileTool initialized with secure root: {self.root_path}")

    def _check_path_safety(self, file_path: str) -> Path:
        """
        Validates the file path to prevent reading. 
        Disable the root_path check if self.unsafe_mode is True.
        """
        # If llm provide a empty file path, it will see the error message
        if not file_path:
            raise ValueError("File path is empty, please check your path configuration")

        input_path = Path(file_path)

        target_path = (self.root_path / input_path).resolve()

        # Path Traversal Check
        if not self.unsafe_mode:
            try:
                target_path.relative_to(self.root_path)
            except ValueError:
                # Access Denied: File path outside the configured root.
                raise ValueError(f"Access Denied: File path '{file_path}' must be inside the configured root: {self.root_path}")
            
        # Existence Check
        if not target_path.exists():
            raise FileNotFoundError(f"File not found at path: {file_path}")
        

        # Is File Check
        if not target_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        return target_path

    def _get_total_lines(self, target_path: Path) -> int:
        """
        Calculate the totol number of lines of a file
        This is a performace-heavy operation, we use it for accurate error reporting.
        """
        try:
            with open(target_path, 'r', encoding='utf-8') as f:
                return sum(1 for line in f)
        except Exception:
            return -1
    
    def run(self, file_path: str, start_line: int = 1, end_line: int = None) -> str:
        """
        Execute the file reading operation with line-based chunking and size limits.

        :param file_path: The path of the file to be read.
        :param start_line: The 1-indexed line number to start reading from.
        :param end_line: The 1-indexed line number to stop reading before (exclusive).
        :return: A string containing the chunked file content or an error message.
        """
        try:
            # Path Validation
            target_path = self._check_path_safety(file_path)

            # Input Validation
            start_line = max(1, start_line)
            if end_line is not None and end_line <= start_line:
                return "ERROR: end_line must be greater than start_line."
            
            effective_end_line = end_line if end_line is not None else float('inf')

            content = []
            lines_read_count = 0

            with open(target_path, 'r', encoding='utf-8') as f:
                # Iterate through file lines 
                for line_number, line in enumerate(f, 1):
                    # A. Apply Start Line Filter
                    if line_number < start_line:
                        continue
                    
                    # B. Apply End Line Filter
                    if line_number >= effective_end_line:
                        break
                    
                    # C. Format and Truncate line
                    line_content = line.rstrip('\n')

                    if len(line_content) > MAX_LINE_CHARS:
                        truncated_content = line_content[:MAX_LINE_CHARS]

                        formatted_line = (
                            f"{line_number}:{truncated_content} "
                            f"[WARNING: Line {line_number} was truncated to {MAX_LINE_CHARS} characters]")
                    else:
                        formatted_line = f"{line_number}:{line_content}"

                    content.append(formatted_line)
                    lines_read_count += 1

                last_line_read = start_line + lines_read_count - 1
                read_content_string = "\n".join(content)

                if lines_read_count == 0:
                    # Only check total lines when no content was read
                    total_lines = self._get_total_lines(target_path)

                    if total_lines == -1:
                        raise Exception("Could not determine total line count due to file system error")

                    if start_line > total_lines and total_lines > 0:
                        return (
                            f"ERROR: Tool excution failed for '{file_path}'. "
                            f"Reason: Requested start_line ({start_line}) is greater than the total lines in file ({total_lines})."
                        )
                    
                    return (
                        f"SUCCESS: Chunk of '{file_path}' (Lines {start_line}-{total_lines}) is empty. "
                        f"Total lines in file: {total_lines}." 
                    )
    
                return (
                    f"SUCCESS: Chunk of '{file_path}' (Lines {start_line}-{last_line_read}):\n"
                    "-------------------------------------------------------------------------- \n"
                    f"{read_content_string}\n"
                    "-------------------------------------------------------------------------- \n"
                )
        except (FileNotFoundError, ValueError) as e:
            return f"ERROR: Tool excution failed for '{file_path}', Reason: {e}"
        except Exception as e:
            return f"UNEXPECTED ERROR: Could not read file '{file_path}'. System message: {e}"
        
# TODO
# Current logic fails to handle large single-line files, with could cause overload of context
# Solution: Requires introducing a 'start_offset' for byte-level reading

# TODO
# Line-Awareness Reading tool for concise reading and editing
# current method is "n:", "n" might save more token but less llm-friendly, an ablation study can be conducted.