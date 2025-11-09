# tests/real_llm/filesystem_tool/test_create_file_llm.py

import pytest
import json
from pathlib import Path


class TestCreateFileWithLLM:
    """Test CreateFileTool with real LLM API calls"""
    
    @pytest.mark.real_llm
    def test_llm_creates_simple_python_file(self, openrouter_client, llm_tools, tool_definitions, tmp_path):
        """
        Scenario: LLM creates a simple Python file
        
        Steps:
        1. Prepare working directory
        2. Send task to LLM: create a Python file
        3. LLM calls create_file tool
        4. Verify file is created with correct content
        """
        # Prepare directory
        (tmp_path / "app").mkdir()
        
        # Task message for LLM
        task_message = """
Please use the create_file tool to create a Python script at 'app/hello.py'.
The script should contain a function named 'hello_world' that prints "Hello, World!".
Make sure the code is complete and can be executed directly.
"""
        
        messages = [
            {"role": "user", "content": task_message}
        ]
        
        system_prompt = """
You are a code generation assistant. You have the following tools available:
1. create_file - Create a new file with content
2. read_file - Read file content
3. modify_file - Modify existing files

Always respond with complete, executable code. Use the tools as needed.
"""
        
        # Call OpenRouter API with tools
        response = openrouter_client.call_with_tools(
            messages=messages,
            tools=tool_definitions,
            system_prompt=system_prompt
        )
        
        print(f"\n📨 LLM Response: {response['content']}")
        print(f"🔧 Tool Calls Count: {len(response['tool_calls'])}")
        
        # Verify LLM called at least one tool
        assert len(response['tool_calls']) > 0, "LLM should call at least one tool"
        
        # Process tool calls
        for tool_call in response['tool_calls']:
            print(f"\n🔍 Tool Called: {tool_call['name']}")
            print(f"   Arguments: {json.dumps(tool_call['arguments'], ensure_ascii=False, indent=2)}")
            
            if tool_call['name'] == 'create_file':
                args = tool_call['arguments']
                
                # Execute tool
                result = llm_tools['create'].run(
                    file_path=args['file_path'],
                    content=args['content'],
                    return_content=True
                )
                
                print(f"\n✅ Tool Execution Result:\n{result}")
                
                # Verify file was created
                file_path = tmp_path / args['file_path']
                assert file_path.exists(), f"File {args['file_path']} should be created"
                
                # Verify file content
                content = file_path.read_text(encoding='utf-8')
                assert 'def' in content or 'function' in content.lower(), "File should contain function definition"
                assert 'hello' in content.lower() or 'world' in content.lower(), "File should contain hello/world"
                
                print(f"\n📄 File Content:\n{content}")
    
    @pytest.mark.real_llm
    def test_llm_creates_and_reads_json_config(self, openrouter_client, llm_tools, tool_definitions, tmp_path):
        """
        Scenario: LLM creates JSON config file, then reads it back
        
        Tests LLM's multi-step reasoning ability
        """
        (tmp_path / "config").mkdir()
        
        task_message = """
Complete the following task using the provided tools:

1. Create a JSON configuration file at 'config/settings.json' with the following fields:
   - app_name: "MyApp"
   - version: "1.0.0"
   - debug: true
   - port: 8000

2. Then use the read_file tool to read the file you just created and verify the content.

Make sure the JSON is valid and properly formatted.
"""
        
        messages = [{"role": "user", "content": task_message}]
        
        system_prompt = "You are a task execution assistant. Use the provided tools to complete the user's request."
        
        # First LLM API call
        response = openrouter_client.call_with_tools(
            messages=messages,
            tools=tool_definitions,
            system_prompt=system_prompt
        )
        
        print(f"\n🤖 LLM Initial Response: {response['content']}")
        
        # Prepare for next turn (if LLM wants to continue)
        messages.append({
            "role": "assistant",
            "content": response['content'],
        })
        
        # Process tool calls
        for tool_call in response['tool_calls']:
            print(f"\n🔍 Tool Called: {tool_call['name']}")
            print(f"   Arguments: {json.dumps(tool_call['arguments'], ensure_ascii=False, indent=2)}")
            
            if tool_call['name'] == 'create_file':
                args = tool_call['arguments']
                result = llm_tools['create'].run(
                    file_path=args.get('file_path'),
                    content=args.get('content'),
                    return_content=False
                )
                print(f"\n✅ create_file Result: {result}")
                
                # Add tool result to messages for LLM's next turn
                messages.append({
                    "role": "user",
                    "content": f"Tool 'create_file' result: {result}"
                })
            
            elif tool_call['name'] == 'read_file':
                args = tool_call['arguments']
                result = llm_tools['read'].run(
                    file_path=args.get('file_path')
                )
                print(f"\n✅ read_file Result: {result[:200]}...")
                
                messages.append({
                    "role": "user",
                    "content": f"Tool 'read_file' result: {result}"
                })
        
        # Verify config file was created
        config_file = tmp_path / "config/settings.json"
        assert config_file.exists(), "Config file should be created"
        
        # Verify JSON format and content
        config_content = json.loads(config_file.read_text())
        assert config_content['app_name'] == 'MyApp', "app_name should be MyApp"
        assert config_content['version'] == '1.0.0', "version should be 1.0.0"
        assert config_content['debug'] is True, "debug should be true"
        assert config_content['port'] == 8000, "port should be 8000"
        
        print(f"\n✨ Test Passed! Config Content: {config_content}")