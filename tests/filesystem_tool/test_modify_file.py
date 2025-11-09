import pytest
from pathlib import Path
from llm_tool_hub.filesystem_tool.modify_file_tool import ModifyFileTool
from llm_tool_hub.filesystem_tool.base_filesystem_tool import CONTEXT_WINDOW_SIZE 
# --- Fixtures and Setup ---

# Initial file content (10 lines of actual content)
INITIAL_CONTENT_LINES = [
    "def function_a():",        # L1
    "    # Implementation of A", # L2
    "    pass",                  # L3
    "",                          # L4 (Empty line)
    "def function_b():",        # L5
    "    # Implementation of B", # L6
    "    return True",           # L7
    "def function_c():",        # L8
    "    print('start')",        # L9
    "    return False"           # L10
]
# Ensure the file ends with a single newline for consistency (Tool should count 10 content lines)
INITIAL_CONTENT_STR = "\n".join(INITIAL_CONTENT_LINES) + "\n" 

@pytest.fixture
def modify_tool(tmp_path: Path) -> ModifyFileTool:
    """Fixture to initialize ModifyFileTool with a temporary root path."""
    return ModifyFileTool(root_path=tmp_path)

@pytest.fixture
def setup_file(tmp_path: Path) -> Path:
    """Fixture to create a standard file for modification tests."""
    file_path = tmp_path / "test_file.py"
    file_path.write_text(INITIAL_CONTENT_STR, encoding='utf-8')
    return file_path

# --- Helper for checking synchronized content (The MOST CRITICAL check) ---
def check_sync_window(result: str, expected_lines_with_numbers: list[str], total_lines: int):
    """
    Checks the structure, line numbers, and content of the synchronized window.
    expected_lines_with_numbers must be formatted as "N:content"
    """
    
    assert "SYNCHRONIZED CONTENT WINDOW" in result
    # FIX: Ensure total_lines matches the tool's calculation (content lines only)
    assert f"Total lines in file now: {total_lines}." in result
    
    # Extract the content block between the separators
    parts = result.split("--------------------------------------------------------------------------")
    assert len(parts) >= 3, "Synchronization block delimiters not found in result."
    content_block = parts[1].strip()
    
    # Extract actual lines, stripping delimiters like "[...]"
    actual_lines = [
        line.strip() 
        for line in content_block.split('\n') 
        if line.strip() and not line.startswith('[') and not line.startswith('NOTE:')
    ]
    
    # Check that the number of returned lines is correct
    assert len(actual_lines) == len(expected_lines_with_numbers), (
        f"Mismatch in lines returned in window. Expected {len(expected_lines_with_numbers)} lines, "
        f"got {len(actual_lines)}.\nActual lines:\n{content_block}"
    )
    
    # Check content and line numbers exactly
    for i, (actual, expected) in enumerate(zip(actual_lines, expected_lines_with_numbers)):
        assert actual == expected, f"Line {i+1} mismatch. Expected: '{expected}', Got: '{actual}'"

# ==============================================================================
# A. Modification Operations (Replacement, Deletion, Insertion)
# ==============================================================================

def test_replace_single_line(modify_tool: ModifyFileTool, setup_file: Path):
    """A.1: Tests replacing a single line (L5 -> L5). Line count remains 10."""
    
    # Replace L5: "def function_b():"
    new_code = "def new_function_b(arg):"
    
    result = modify_tool.run(str(setup_file.name), start_line=5, end_line=5, new_content=new_code)
    
    assert "Operation: replaced 1 lines" in result
    
    # Check sync window: L1 to L10
    expected_sync_lines = [
        "1:def function_a():",
        "2:    # Implementation of A",
        "3:    pass",
        "4:",
        "5:def new_function_b(arg):", # The replaced line
        "6:    # Implementation of B",
        "7:    return True",
        "8:def function_c():",
        "9:    print('start')",
        "10:    return False",
    ]
    # FIX: total_lines is 10
    check_sync_window(result, expected_sync_lines, 10) 


def test_replace_multi_line_and_change_count(modify_tool: ModifyFileTool, setup_file: Path):
    """A.2: Tests replacing L5-L6 with 4 new lines. (Line count increases by 2, total 12)."""
    
    # Replace L5-L6 (2 lines) with new 4-line content
    new_code = "def new_func_d():\n    new_line_1\n    new_line_2\n    return 'D'"
    
    result = modify_tool.run(str(setup_file.name), start_line=5, end_line=6, new_content=new_code)
    
    # Check status and operation message
    assert "Operation: replaced 2 lines" in result
    assert "with 4 new lines" in result
    
    # New total lines: 10 - 2 + 4 = 12
    
    # Check sync window: Lines L1 to L12
    expected_sync_lines = [
        "1:def function_a():",
        "2:    # Implementation of A",
        "3:    pass",
        "4:",
        "5:def new_func_d():",        # NEW
        "6:    new_line_1",          # NEW
        "7:    new_line_2",          # NEW
        "8:    return 'D'",          # NEW
        "9:    return True",         # Shifted L7
        "10:def function_c():",      # Shifted L8
        "11:    print('start')",     # Shifted L9
        "12:    return False",        # Shifted L10
    ]
    # FIX: total_lines is 12
    check_sync_window(result, expected_sync_lines, 12)


def test_insert_before_line(modify_tool: ModifyFileTool, setup_file: Path):
    """A.3: Tests inserting 3 lines before L5. (Line count increases by 3, total 13)."""
    
    # Insert before L5
    new_code = "### NEW BLOCK ###\nINSERTED_LINE_1\nINSERTED_LINE_2"
    
    # end_line=4 < start_line=5 signals insertion mode
    result = modify_tool.run(str(setup_file.name), start_line=5, end_line=4, new_content=new_code)
    
    assert "Operation: inserted 3 lines before line 5" in result
    
    # New total lines: 10 + 3 = 13
    
    # Check sync window: L1-L13
    expected_sync_lines = [
        "1:def function_a():",
        "2:    # Implementation of A",
        "3:    pass",
        "4:",
        "5:### NEW BLOCK ###",      # NEW
        "6:INSERTED_LINE_1",        # NEW
        "7:INSERTED_LINE_2",        # NEW
        "8:def function_b():",      # Shifted L5
        "9:    # Implementation of B", # Shifted L6
        "10:    return True",        # Shifted L7
        "11:def function_c():",      # Shifted L8
        "12:    print('start')",     # Shifted L9
        "13:    return False",       # Shifted L10
    ]
    # FIX: total_lines is 13
    check_sync_window(result, expected_sync_lines, 13)


def test_delete_multi_line(modify_tool: ModifyFileTool, setup_file: Path):
    """A.4: Tests deleting 3 lines (L2-L4). (Line count decreases by 3, total 7)."""
    
    # Delete L2, L3, L4 (empty content)
    result = modify_tool.run(str(setup_file.name), start_line=2, end_line=4, new_content="")
    
    assert "Operation: deleted 3 lines" in result
    
    # New total lines: 10 - 3 = 7
    
    # Check sync window: Focusing on the change (L2-L4 removed) and the shifted lines (L2+)
    expected_sync_lines = [
        "1:def function_a():",      # L1 (Context before)
        "2:def function_b():",      # Shifted L5 (Context after)
        "3:    # Implementation of B", # Shifted L6
        "4:    return True",        # Shifted L7
        "5:def function_c():",      # Shifted L8
        "6:    print('start')",     # Shifted L9
        "7:    return False",       # Shifted L10
    ]
    # FIX: total_lines is 7
    check_sync_window(result, expected_sync_lines, 7)


# ==============================================================================
# B. Edge Cases and Boundary Tests
# ==============================================================================

def test_append_at_end(modify_tool: ModifyFileTool, setup_file: Path):
    """B.1: Tests appending lines at the very end of the file (Insertion after L10)."""
    
    # The file has 10 lines.
    # Insertion at L11 (after L10)
    new_code = "print('final_line')"
    
    # FIX: start_line=11, end_line=10 signals insertion at the end
    result = modify_tool.run(str(setup_file.name), start_line=11, end_line=10, new_content=new_code)
    
    # FIX: Assertion message must match the new start_line
    assert "Operation: inserted 1 lines before line 11" in result
    
    # New total lines: 10 + 1 = 11
    final_content = setup_file.read_text().splitlines()
    assert final_content[-1] == "print('final_line')"
    assert len(final_content) == 11 
    
    # Check sync window: Should show the last 5 original lines and the 1 new line
    expected_sync_lines = [
        #"[...]", # Start of truncation
        "6:    # Implementation of B",
        "7:    return True",
        "8:def function_c():",
        "9:    print('start')",
        "10:    return False",
        "11:print('final_line')" 
    ]
    # total_lines is 11
    check_sync_window(result, expected_sync_lines, 11)
    

def test_modify_file_not_exist_fails(modify_tool: ModifyFileTool):
    """B.2: Tests failure when trying to modify a non-existent file (must_exist=True)."""
    
    result = modify_tool.run("non_existent.txt", start_line=1, end_line=1, new_content="test")
    
    assert result.startswith("ERROR:")
    assert "Reason: File not found at path:" in result

def test_modify_file_traversal_fails(modify_tool: ModifyFileTool, setup_file: Path, tmp_path: Path):
    """B.3: Tests path traversal security (../../)."""
    
    # Set tool root to a subdirectory
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    tool = ModifyFileTool(root_path=subdir)
    
    # Try to modify the file created outside the root_path
    result = tool.run(f"../{setup_file.name}", start_line=1, end_line=1, new_content="test")
    
    assert result.startswith("ERROR:")
    assert "Access Denied: File path" in result
    
# ==============================================================================
# C. Function Calling Metadata Test (Required by the overall SOP)
# ==============================================================================

def test_modify_file_tool_metadata(modify_tool: ModifyFileTool):
    """C.1: Tests that the tool's metadata (for Function Calling) is correctly defined."""
    
    assert modify_tool.name == "modify_file"
    assert "**[SINGLE FILE OPERATION]**" in modify_tool.description
    assert "SYNCHRONIZED CONTENT WINDOW" in modify_tool.description
    
    parameters = modify_tool.parameters
    
    assert parameters["type"] == "object"
    assert "file_path" in parameters["required"]
    assert "start_line" in parameters["required"]
    assert "end_line" in parameters["required"]
    
    # Check start_line/end_line constraints
    assert parameters["properties"]["start_line"]["type"] == "integer"
    assert parameters["properties"]["start_line"]["minimum"] == 1
    
    assert parameters["properties"]["end_line"]["type"] == "integer"
    assert parameters["properties"]["end_line"]["minimum"] == 1
    
    # Check new_content description and default
    new_content_prop = parameters["properties"]["new_content"]
    assert new_content_prop["type"] == "string"
    assert 'Use an empty string ("") to delete' in new_content_prop["description"]
    assert new_content_prop["default"] == ""