# tests/real_llm/filesystem_tool/test_read_file_llm.py

import pytest
import json
from pathlib import Path


class TestReadFileWithLLM:
    """Test ReadFileTool with real LLM API calls"""
    
    @pytest.mark.real_llm
    def test_llm_reads_python_and_extracts_values(self, openrouter_client, llm_tools, tool_definitions, tmp_path):
        """
        Scenario: LLM reads a Python file with calculations and extracts exact numeric values
        
        Verification: Check that LLM returns the exact computed values
        """
        (tmp_path / "scripts").mkdir()
        script_file = tmp_path / "scripts" / "calculator.py"
        script_content = '''a = 10
b = 5

result_add = a + b
result_multiply = a * b
result_subtract = a - b
'''
        script_file.write_text(script_content, encoding='utf-8')
        
        task_message = """
Read the file at 'scripts/calculator.py' and answer:
1. What is result_add?
2. What is result_multiply?
3. What is result_subtract?

Answer ONLY in this format:
result_add: [number]
result_multiply: [number]
result_subtract: [number]
"""
        
        messages = [{"role": "user", "content": task_message}]
        
        system_prompt = """
You are a Python code analyzer. Extract exact numeric values.
Answer ONLY in the requested format.
"""
        
        # Define tool executors
        tool_executors = {
            'read_file': lambda file_path, start_line=1, end_line=None: llm_tools['read'].run(
                file_path=file_path, start_line=start_line, end_line=end_line
            )
        }
        
        response = openrouter_client.call_with_tools(
            messages=messages,
            tools=tool_definitions,
            system_prompt=system_prompt,
            tool_executors=tool_executors
        )
        
        print(f"\n🤖 LLM Response:\n{response['content']}")
        
        # Verify tool was called
        assert any(tc['name'] == 'read_file' for tc in response['tool_calls']), \
            "LLM should call read_file tool"
        
        # Verify exact answers
        llm_response = response['content']
        
        # Check result_add (10 + 5 = 15)
        assert '15' in llm_response and 'result_add' in llm_response, \
            f"LLM should answer result_add=15, got: {llm_response}"
        
        # Check result_multiply (10 * 5 = 50)
        assert '50' in llm_response and 'result_multiply' in llm_response, \
            f"LLM should answer result_multiply=50, got: {llm_response}"
        
        # Check result_subtract (10 - 5 = 5)
        assert '5' in llm_response and 'result_subtract' in llm_response, \
            f"LLM should answer result_subtract=5, got: {llm_response}"
        
        print(f"\n✨ Test Passed! LLM extracted correct values: 15, 50, 5")
    
    @pytest.mark.real_llm
    def test_llm_reads_config_and_extracts_values(self, openrouter_client, llm_tools, tool_definitions, tmp_path):
        """
        Scenario: LLM reads a config file and extracts specific values
        
        Verification: Check exact values match the file content
        """
        (tmp_path / "config").mkdir()
        
        config_file = tmp_path / "config" / "app.conf"
        config_content = '''server_port=8080
max_workers=16
timeout_seconds=60
debug_mode=false
api_key=sk_test_abc123xyz789
'''
        config_file.write_text(config_content, encoding='utf-8')
        
        task_message = """
Read the config file at 'config/app.conf' and answer:
1. What is server_port?
2. What is max_workers?
3. What is timeout_seconds?

Answer ONLY in this format:
server_port: [value]
max_workers: [value]
timeout_seconds: [value]
"""
        
        messages = [{"role": "user", "content": task_message}]
        
        system_prompt = """
You are a config file parser. Extract exact values.
Answer ONLY in the requested format, no extra text.
"""
        
        tool_executors = {
            'read_file': lambda file_path, start_line=1, end_line=None: llm_tools['read'].run(
                file_path=file_path, start_line=start_line, end_line=end_line
            )
        }
        
        response = openrouter_client.call_with_tools(
            messages=messages,
            tools=tool_definitions,
            system_prompt=system_prompt,
            tool_executors=tool_executors
        )
        
        print(f"\n🤖 LLM Response:\n{response['content']}")
        
        # Verify tool was called
        assert any(tc['name'] == 'read_file' for tc in response['tool_calls']), \
            "LLM should call read_file"
        
        llm_response = response['content']
        
        # Verify exact values
        assert 'server_port: 8080' in llm_response or 'server_port:8080' in llm_response.replace(' ', ''), \
            f"LLM should answer server_port=8080, got: {llm_response}"
        
        assert 'max_workers: 16' in llm_response or 'max_workers:16' in llm_response.replace(' ', ''), \
            f"LLM should answer max_workers=16, got: {llm_response}"
        
        assert 'timeout_seconds: 60' in llm_response or 'timeout_seconds:60' in llm_response.replace(' ', ''), \
            f"LLM should answer timeout_seconds=60, got: {llm_response}"
        
        print(f"\n✨ Test Passed! LLM extracted correct values: 8080, 16, 60")
    
    @pytest.mark.real_llm
    def test_llm_counts_specific_items_in_file(self, openrouter_client, llm_tools, tool_definitions, tmp_path):
        """
        Scenario: LLM reads a file and counts occurrences of a specific pattern
        
        Verification: Check the exact count matches reality
        """
        (tmp_path / "logs").mkdir()
        
        log_file = tmp_path / "logs" / "events.log"
        # File with exactly 5 lines containing "ERROR"
        log_content = '''INFO: System started
ERROR: Database failed
INFO: Retrying
ERROR: Timeout occurred
WARNING: Memory high
ERROR: Connection lost
DEBUG: Checking status
ERROR: Retry failed
INFO: System shutdown
ERROR: Final error
'''
        log_file.write_text(log_content, encoding='utf-8')
        
        task_message = """
Read the file at 'logs/events.log' and count:
How many lines contain the word "ERROR"?

Answer ONLY with the number, nothing else.
"""
        
        messages = [{"role": "user", "content": task_message}]
        
        system_prompt = """
You are a log analyzer. Count occurrences precisely.
Answer ONLY with a single number, nothing else.
"""
        
        tool_executors = {
            'read_file': lambda file_path, start_line=1, end_line=None: llm_tools['read'].run(
                file_path=file_path, start_line=start_line, end_line=end_line
            )
        }
        
        response = openrouter_client.call_with_tools(
            messages=messages,
            tools=tool_definitions,
            system_prompt=system_prompt,
            tool_executors=tool_executors
        )
        
        print(f"\n🤖 LLM Response:\n{response['content']}")
        
        # Verify tool was called
        assert any(tc['name'] == 'read_file' for tc in response['tool_calls']), \
            "LLM should call read_file"
        
        llm_response = response['content'].strip()
        
        # Count actual errors in the log file
        actual_error_count = log_content.count('ERROR')
        print(f"✓ Actual ERROR count in file: {actual_error_count}")
        
        # Verify LLM's count
        assert str(actual_error_count) in llm_response, \
            f"LLM should answer {actual_error_count}, got: {llm_response}"
        
        print(f"\n✨ Test Passed! LLM correctly counted {actual_error_count} ERROR lines")
    
    @pytest.mark.real_llm
    def test_llm_identifies_file_structure(self, openrouter_client, llm_tools, tool_definitions, tmp_path):
        """
        Scenario: LLM reads a CSV file and identifies column names and row count
        
        Verification: Check the identified structure matches the file
        """
        (tmp_path / "data").mkdir()
        
        csv_file = tmp_path / "data" / "users.csv"
        csv_content = '''id,name,email,role
1,alice@example.com,alice,admin
2,bob@example.com,bob,user
3,charlie@example.com,charlie,user
4,diana@example.com,diana,user
5,eve@example.com,eve,admin
'''
        csv_file.write_text(csv_content, encoding='utf-8')
        
        task_message = """
Read the CSV file at 'data/users.csv' and answer:
1. What are the column names? (List them separated by commas)
2. How many data rows are there (excluding header)?

Answer in this format:
columns: [list]
rows: [number]
"""
        
        messages = [{"role": "user", "content": task_message}]
        
        system_prompt = """
You are a CSV analyzer. Identify columns and count rows accurately.
Answer ONLY in the requested format.
"""
        
        tool_executors = {
            'read_file': lambda file_path, start_line=1, end_line=None: llm_tools['read'].run(
                file_path=file_path, start_line=start_line, end_line=end_line
            )
        }
        
        response = openrouter_client.call_with_tools(
            messages=messages,
            tools=tool_definitions,
            system_prompt=system_prompt,
            tool_executors=tool_executors
        )
        
        print(f"\n🤖 LLM Response:\n{response['content']}")
        
        # Verify tool was called
        assert any(tc['name'] == 'read_file' for tc in response['tool_calls']), \
            "LLM should call read_file"
        
        llm_response = response['content']
        
        # Verify columns are identified
        expected_columns = ['id', 'name', 'email', 'role']
        for col in expected_columns:
            assert col.lower() in llm_response.lower(), \
                f"LLM should mention column '{col}', got: {llm_response}"
        
        # Verify row count (5 data rows)
        assert '5' in llm_response and 'rows' in llm_response, \
            f"LLM should identify 5 data rows, got: {llm_response}"
        
        print(f"\n✨ Test Passed! LLM correctly identified columns and 5 data rows")
