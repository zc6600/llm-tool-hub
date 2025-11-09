# tests/real_llm/shell_tool/test_shell_tool_llm.py

import pytest
import json
from pathlib import Path


class TestShellToolWithLLM:
    """Test ShellTool independently with real LLM API calls (no other tool dependencies)"""
    
    @pytest.mark.real_llm
    def test_llm_executes_echo_command(self, openrouter_client, tmp_path):
        """
        Scenario: LLM uses shell_tool to execute echo command
        
        Verification: Check that shell_tool returns the correct output
        (not verifying LLM's text response, but the tool's actual result)
        """
        from llm_tool_hub.shell_tool.shell_tool import ShellTool
        
        # Initialize only shell_tool (no other tools)
        shell_tool = ShellTool(root_path=str(tmp_path))
        
        # Define only shell_tool in tool definitions
        tool_definitions = [shell_tool.get_metadata()]
        
        task_message = """
Use the shell_tool to execute:
echo "line1"
echo "line2"
echo "line3"
echo "line4"
echo "line5"
"""
        
        messages = [{"role": "user", "content": task_message}]
        
        system_prompt = """
You are a shell command executor. Use shell_tool to run the commands provided.
"""
        
        response = openrouter_client.call_with_tools(
            messages=messages,
            tools=tool_definitions,
            system_prompt=system_prompt
        )
        
        print(f"\n🤖 LLM Response: {response['content']}")
        print(f"🔧 Tool Calls: {len(response['tool_calls'])}")
        
        # Verify shell_tool was called
        assert len(response['tool_calls']) > 0, "LLM should call shell_tool"
        
        # Verify the tool executed correctly
        tool_outputs = []
        for tool_call in response['tool_calls']:
            if tool_call['name'] == 'shell_tool':
                args = tool_call['arguments']
                print(f"\n🔍 Shell Command: {args.get('command')}")
                
                result = shell_tool.run(command=args.get('command'))
                print(f"✅ Command Result: {result}")
                tool_outputs.append(result)
        
        # Verify tool outputs contain expected text
        combined_output = '\n'.join(tool_outputs)
        assert 'line1' in combined_output and 'line5' in combined_output, \
            f"Tool should have executed echo commands, got: {combined_output}"
        
        print(f"\n✨ Test Passed! shell_tool executed echo commands successfully")
    
    @pytest.mark.real_llm
    def test_llm_executes_pwd_command(self, openrouter_client, tmp_path):
        """
        Scenario: LLM uses shell_tool to execute pwd command
        
        Verification: Check that shell_tool returns a valid path
        """
        from llm_tool_hub.shell_tool.shell_tool import ShellTool
        
        shell_tool = ShellTool(root_path=str(tmp_path))
        tool_definitions = [shell_tool.get_metadata()]
        
        task_message = """
Use the shell_tool to execute:
pwd
"""
        
        messages = [{"role": "user", "content": task_message}]
        
        system_prompt = "You are a shell command executor. Use shell_tool to run commands."
        
        response = openrouter_client.call_with_tools(
            messages=messages,
            tools=tool_definitions,
            system_prompt=system_prompt
        )
        
        print(f"\n🤖 LLM Response: {response['content']}")
        
        assert len(response['tool_calls']) > 0, "LLM should call shell_tool"
        
        # Verify tool executed
        tool_executed = False
        for tool_call in response['tool_calls']:
            if tool_call['name'] == 'shell_tool':
                tool_executed = True
                args = tool_call['arguments']
                result = shell_tool.run(command=args.get('command'))
                print(f"✅ pwd output: {result}")
                
                # Verify result contains a path
                assert '/' in result or 'Users' in result, \
                    f"pwd should return a path, got: {result}"
        
        assert tool_executed, "shell_tool should have been executed"
        print(f"\n✨ Test Passed! shell_tool executed pwd successfully")
    
    @pytest.mark.real_llm
    def test_llm_executes_arithmetic_command(self, openrouter_client, tmp_path):
        """
        Scenario: LLM uses shell_tool to perform arithmetic using expr
        
        Verification: Check that shell_tool returns correct calculation result
        """
        from llm_tool_hub.shell_tool.shell_tool import ShellTool
        
        shell_tool = ShellTool(root_path=str(tmp_path))
        tool_definitions = [shell_tool.get_metadata()]
        
        task_message = """
Use the shell_tool to execute:
expr 100 + 50
"""
        
        messages = [{"role": "user", "content": task_message}]
        
        system_prompt = "You are a shell command executor. Use shell_tool to run commands."
        
        response = openrouter_client.call_with_tools(
            messages=messages,
            tools=tool_definitions,
            system_prompt=system_prompt
        )
        
        print(f"\n🤖 LLM Response: {response['content']}")
        
        assert len(response['tool_calls']) > 0, "LLM should call shell_tool"
        
        # Verify tool output
        tool_executed = False
        for tool_call in response['tool_calls']:
            if tool_call['name'] == 'shell_tool':
                tool_executed = True
                args = tool_call['arguments']
                result = shell_tool.run(command=args.get('command'))
                print(f"✅ expr result: {result}")
                
                # Verify result is 150
                assert '150' in result, \
                    f"expr 100 + 50 should return 150, got: {result}"
        
        assert tool_executed, "shell_tool should have been executed"
        print(f"\n✨ Test Passed! shell_tool calculated 100 + 50 = 150")
    
    @pytest.mark.real_llm
    def test_llm_creates_and_verifies_files(self, openrouter_client, tmp_path):
        """
        Scenario: LLM uses shell_tool to create files
        
        Verification: Verify that files are actually created on filesystem
        """
        from llm_tool_hub.shell_tool.shell_tool import ShellTool
        import os
        
        shell_tool = ShellTool(root_path=str(tmp_path))
        tool_definitions = [shell_tool.get_metadata()]
        
        task_message = f"""
Use the shell_tool to create a test file named 'test.txt' in {tmp_path}.
Execute: touch {tmp_path}/test.txt
"""
        
        messages = [{"role": "user", "content": task_message}]
        
        system_prompt = "You are a shell command executor. Use shell_tool to run commands."
        
        response = openrouter_client.call_with_tools(
            messages=messages,
            tools=tool_definitions,
            system_prompt=system_prompt
        )
        
        print(f"\n🤖 LLM Response: {response['content']}")
        
        assert len(response['tool_calls']) > 0, "LLM should call shell_tool"
        
        # Execute tool calls to create files
        for tool_call in response['tool_calls']:
            if tool_call['name'] == 'shell_tool':
                args = tool_call['arguments']
                result = shell_tool.run(command=args.get('command'))
                print(f"✅ Command: {args.get('command')}")
                print(f"   Result: {result[:100]}...")
        
        # Verify file was actually created on filesystem
        test_file = os.path.join(tmp_path, 'test.txt')
        assert os.path.exists(test_file), f"File should exist at {test_file}"
        
        print(f"\n✨ Test Passed! shell_tool successfully created file")
