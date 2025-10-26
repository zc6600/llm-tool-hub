# src/llm_tool_hub/filesystem_tool/create_file_tool.py

import logging
from typing import Dict, Any, Union
from pathlib import Path
from .base_filesystem_tool import BaseFileSystemTool

logger = logging.getLogger(__name__)

class CreateFileTool(BaseFileSystemTool):
    """
    A tool to safely create a NEW text file in the project's working directory.
    If the file already exists, the operation will fail to prevent accidental overwrites.
    """

    name: str = "create_file"
    description: str = (
        "Create a NEW file and write the content to it. "
        "The operation will fail if the file already exists."
        "To modify existing files, try to use 'modify_tool' or delete the original tool if you are sure the file should be replaced."
    )
    
    # JSON Schema fo the 'run' method parameters
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": (
                    "The relative path to the New file from the root_path. "
                    "Example: 'data/new_file.txt'"
                ),
            },
            "content": {
                "type": "string",
                "description": "The content to write into the new file."
            },
            "return_content": {
                    "type": "boolean",
                    "description": (
                        "If true, returns the content written to the file in the response. "
                        "Defaults to false."
                    ),
                    "default": True,
            },  
        },
        "required": ["file_path", "content"]
    }

    def run(self, file_path: str, content: str, return_content: bool = True) -> str:
        """
        Creates a new file and writes the provided content to it. Fails if file exists.
        
        :param file_path: The relative path to the target file.
        :param content: The full content string to write.
        :param return_content: If True, returns the content with line numbers for synchronization.
        :return: A success message, potentially including the read content, or an error.
        """
        try:
            # Path Validation: Use the common safety checker.
            # CRITICAL: must_exist=False ensures the tool FAILS if the file ALREADY EXISTS.
            # allow_dir=False ensures we don't try to write to a directory.
            target_path = self._check_path_safety(
                file_path, 
                must_exist=False, 
                allow_dir=False
            )

            # 1. Perform Write Operation
            # Using 'w' mode after safety check ensures safe creation.
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # 2. Prepare Success Message
            line_count = len(content.splitlines())
            base_success_message = (
                f"SUCCESS: File '{file_path}' successfully created with {line_count} lines of initial content."
            )

            # 3. Handle Content Return based on LLM choice
            if return_content:
                # Read back the content and format with line numbers (Synchronization Step)
                formatted_content_lines = []
                
                # Re-open in read mode to handle clean line parsing
                with open(target_path, 'r', encoding='utf-8') as f_read:
                    for line_number, line in enumerate(f_read, 1):
                        line_content = line.rstrip('\n')
                        formatted_content_lines.append(f"{line_number}:{line_content}")
                
                read_content_string = "\n".join(formatted_content_lines)

                # Return detailed success message with synced content
                return (
                    f"{base_success_message} Content with line numbers for subsequent modification:\n"
                    "-------------------------------------------------------------------------- \n"
                    f"{read_content_string}\n"
                    "-------------------------------------------------------------------------- \n"
                )
            else:
                # Return simple success message (Token Saving Mode)
                return base_success_message

        # Catch specific errors thrown by BaseFileSystemTool._check_path_safety or open/write
        except FileNotFoundError as e:
            # This is typically caught by Check 4 (Parent directory doesn't exist)
            return f"ERROR: Tool execution failed for '{file_path}'. Reason: Parent directory not found or general I/O error: {e}"
        except ValueError as e:
            # This is typically caught by Check 2 (File already exists) or Check 3 (Path is a directory)
            return f"ERROR: Tool execution failed for '{file_path}'. Reason: {e}"
        except Exception as e:
            return f"UNEXPECTED ERROR: Could not create file '{file_path}'. System message: {e}"