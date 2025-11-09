import logging
from typing import Dict, Any, Union
from pathlib import Path
from .base_filesystem_tool import BaseFileSystemTool

logger = logging.getLogger(__name__)

class ModifyFileTool(BaseFileSystemTool):
    """
    A tool to safely modify the content of an existing file by replacing, 
    inserting, or deleting lines within a specified range.
    It returns a small content window around the change to synchronize line numbers 
    with the LLM's internal state.
    """

    # --- 1. Required Metadata ---
    name: str = "modify_file"
    description: str = (
        "**[SINGLE FILE OPERATION]** Modifies an EXISTING file by replacing, inserting, or deleting content "
        "within a specified 1-indexed line range. "
        "The operation requires the file to exist and the change to be precisely defined. "
        "CRITICAL: Because line numbers may change after modification, the tool will return a "
        "**SYNCHRONIZED CONTENT WINDOW** with the new, correct line numbers for the modified area. "
        "The LLM MUST use these new line numbers for any subsequent modifications to the same file."
    )
    
    # JSON Schema for the 'run' method parameters
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "The relative path to the EXISTING file to be modified. Example: 'src/main.py'",
            },
            "start_line": {
                "type": "integer",
                "description": "The 1-indexed line number where the modification (replacement/deletion/insertion) should begin.",
                "minimum": 1,
            },
            "end_line": {
                "type": "integer",
                "description": (
                    "The 1-indexed line number where the modification should end (inclusive for replacement/deletion). "
                    "Set equal to start_line for single-line replacement. "
                    "If end_line < start_line, the tool will perform insertion *before* start_line."
                ),
                "minimum": 1,
            },
            "new_content": {
                "type": "string",
                "description": (
                    "The new content to be inserted or to replace the old content in the specified range. "
                    "Use an empty string (\"\") to delete the specified line range."
                ),
                "default": "",
            },
        },
        "required": ["file_path", "start_line", "end_line"]
    }
    

    # --- 3. Core Modification Logic ---
    def run(self, 
            file_path: str, 
            start_line: int, 
            end_line: int, 
            new_content: str = "") -> str:
        """
        Executes the file modification based on the specified line range and content.
        """
        try:
            # 3.1 Path Validation
            # CRITICAL: must_exist=True ensures we only modify existing files.
            target_path = self._check_path_safety(
                file_path, 
                must_exist=True, 
                allow_dir=False
            )
            
            # 3.2 Input Validation
            if start_line < 1 or end_line < 0: # end_line can be 0 for insertion before line 1
                 return "ERROR: start_line must be >= 1. end_line must be >= 0."
            
            # 3.3 Read File
            original_lines = self._get_lines(target_path)
            total_lines = len(original_lines)
            new_content_lines = new_content.splitlines()

            # Initialize variables needed for synchronization feedback
            modified_start_line = start_line 
            new_lines_count = len(new_content_lines) 

            # 3.4 Determine Operation Type and Boundaries
            
            # If start_line > total_lines + 1, it's out of bounds for insertion/appending.
            if start_line > total_lines + 1:
                return (
                    f"ERROR: Cannot modify lines. Requested start_line ({start_line}) "
                    f"is beyond the file's current end ({total_lines})."
                )

            # Case A: Insertion (end_line < start_line)
            if end_line < start_line:
                # The operation is an insertion BEFORE start_line
                insert_index = start_line - 1 # 0-indexed position to insert BEFORE
                
                # Check 1: Insertion before line 1 (start_line=1, end_line=0) is allowed.
                if insert_index < 0: 
                    # This should be covered by input validation, but as a safety net:
                    return "ERROR: Invalid line range for insertion. start_line must be >= 1."
                
                # Perform Insertion
                modified_lines = original_lines[:insert_index] + new_content_lines + original_lines[insert_index:]
                operation = f"inserted {len(new_content_lines)} lines before line {start_line}"
                
            # Case B: Replacement or Deletion (end_line >= start_line)
            else:
                # 0-indexed slice boundaries
                start_index = start_line - 1
                end_index = end_line # Python slices are exclusive at the end

                # The range of lines to be removed/replaced (handle potential out-of-bounds end_line)
                # If end_line > total_lines, we replace up to the end of the file.
                lines_to_remove = original_lines[start_index:min(end_index, total_lines)]
                lines_removed = len(lines_to_remove)
                
                # Perform Replacement/Deletion
                modified_lines = original_lines[:start_index] + new_content_lines + original_lines[end_index:]

                if not new_content_lines: # Deletion (new_content is empty)
                    operation = f"deleted {lines_removed} lines (lines {start_line}-{start_line + lines_removed - 1})"
                    new_lines_count = 0 # No new lines were added by deletion
                else: # Replacement
                    operation = (
                        f"replaced {lines_removed} lines (lines {start_line}-{start_line + lines_removed - 1}) "
                        f"with {len(new_content_lines)} new lines"
                    )

            # 3.5 Write Back to File (Atomically replace file content)
            
            # Join lines back with newline character for writing. 
            # We append a final newline only if the new content isn't empty and the last line wasn't empty.
            new_content_to_write = '\n'.join(modified_lines)# + ('\n' if modified_lines and not modified_lines[-1].endswith('\n') else '')

            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(new_content_to_write)
                
            new_total_lines = len(modified_lines)
            
            # 3.6 Success Message and Synchronization Return
            
            base_success_message = (
                f"SUCCESS: File '{file_path}' successfully modified. Operation: {operation}."
            )
            
            # Always call the synchronization function to provide new line numbers
            sync_content = self._format_modified_content(
                target_path=target_path,
                new_total_lines=new_total_lines,
                modified_start_line=modified_start_line,
                new_lines_count=new_lines_count,
            )
            
            return f"{base_success_message}\n{sync_content}"

        # 3.7 Error Handling (Unified)
        except (FileNotFoundError, ValueError, IOError) as e:
            return f"ERROR: Tool execution failed for '{file_path}'. Reason: {e}"
        except Exception as e:
            return f"UNEXPECTED ERROR: Could not modify file '{file_path}'. System message: {e}"

