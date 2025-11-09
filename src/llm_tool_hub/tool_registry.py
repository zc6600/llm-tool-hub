# src/llm_tool_hub/tool_registry.py

import logging
from typing import List, Dict, Any, Type, Union
from .base_tool import BaseTool # 假设 BaseTool 是通用基类

logger = logging.getLogger(__name__)

class ToolRegistry:
    """
    一个中央注册中心，用于管理和适配工具，以便集成到 LLM Agent 框架中。

    它负责将 BaseTool 实例转换为标准的 JSON Schema 描述，并提供统一的执行接口。
    """

    def __init__(self, tools: List[BaseTool]):
        """
        使用开发者提供的 BaseTool 实例列表初始化注册中心。

        :param tools: 开发者选择并初始化的 BaseTool 对象列表。
        """
        # 将工具列表转换为字典，便于通过名称快速查找
        self.tools: Dict[str, BaseTool] = {}
        for tool in tools:
            if not tool.name:
                raise ValueError(f"Tool instance of type {type(tool).__name__} must define a 'name' attribute.")
            if tool.name in self.tools:
                logger.warning(f"Duplicate tool name registered: {tool.name}. Skipping the duplicate instance.")
                continue
            self.tools[tool.name] = tool
            logger.debug(f"Tool registered: {tool.name}")


    @staticmethod
    def _create_json_schema(tool_class: Type[BaseTool]) -> Dict[str, Any]:
        """
        [内部方法] 将 BaseTool 的元数据转换为 LLM API 兼容的 JSON Schema 格式。

        :param tool_class: BaseTool 的子类（例如 ShellTool）。
        :return: 标准的工具描述字典（符合 OpenAI/Gemini 规范）。
        """
        if not tool_class.parameters or tool_class.parameters.get("type") != "object":
            logger.warning(
                f"Tool '{tool_class.name}' has invalid or missing 'parameters' definition. "
                "Defaulting to an empty parameters object."
            )
        
        # 构建标准的 function calling 格式
        schema = {
            "type": "function",
            "function": {
                "name": tool_class.name,
                "description": tool_class.description,
                # 确保 parameters 至少是一个有效的对象
                "parameters": tool_class.parameters if tool_class.parameters and tool_class.parameters.get("type") == "object" else {"type": "object", "properties": {}},
            }
        }
        return schema

    def get_tool_descriptions(self) -> List[Dict[str, Any]]:
        """
        返回所有已注册工具的标准 JSON Schema 描述列表。
        这是 Agent 框架集成您的工具集的主要入口。
        """
        descriptions = []
        for tool in self.tools.values():
            descriptions.append(self._create_json_schema(type(tool)))
        return descriptions

    def get_tool_instance(self, name: str) -> BaseTool:
        """
        [内部/外部] 通过工具名称检索已初始化的工具实例。

        :param name: 要检索的工具的名称（例如 'shell_tool'）。
        :return: BaseTool 实例。
        :raises ValueError: 如果工具未注册。
        """
        if name not in self.tools:
            raise ValueError(f"Tool '{name}' is not registered in the ToolRegistry.")
        return self.tools[name]

    def execute_tool_call(self, tool_name: str, **kwargs) -> str:
        """
        统一的工具执行方法。Agent 框架解析 LLM 的工具调用后，应调用此方法。

        :param tool_name: LLM 要求执行的工具名称。
        :param kwargs: LLM 为该工具提供的参数（作为关键字参数）。
        :return: 工具的 run 方法返回的字符串结果。
        """
        try:
            tool_instance = self.get_tool_instance(tool_name)
            
            # 使用 **kwargs 将 LLM 提供的参数直接传递给工具的 run 方法
            logger.info(f"Executing tool: {tool_name} with args: {kwargs}")
            
            result = tool_instance.run(**kwargs)
            
            logger.info(f"Tool {tool_name} executed successfully. Result length: {len(result)}")
            return result
        
        except ValueError as e:
            # 捕获 get_tool_instance 抛出的错误
            return f"ERROR: Tool execution failed. Reason: {e}"
        except TypeError as e:
            # 捕获 run 方法因参数不匹配而导致的错误（LLM 提供了错误的参数）
            return f"ERROR: Tool execution failed. Invalid arguments for '{tool_name}'. Details: {e}"
        except Exception as e:
            # 捕获工具 run 方法中未处理的其他运行时错误
            logger.error(f"Unexpected runtime error during execution of {tool_name}: {e}")
            return f"FATAL ERROR: An unexpected error occurred during tool execution: {type(e).__name__}: {str(e)}"