# 工具系统
# 提供 @tool 装饰器、Tool 类、ToolRegistry 类。
# 自动从函数签名生成 JSON Schema，支持同步和异步函数。

import inspect
from typing import get_type_hints
import jsonschema

from .errors import ToolNotFoundError, ToolExecutionError

# 工具注册表
_TYPE_MAPPING = {
    int: "integer",
    float: "number",
    str: "string",
    bool: "boolean",
    list: "array",
    dict: "object",
}

# 工具类
class Tool:
    # 工具类，封装了工具的名称、描述和参数 schema
    def __init__(self, func):
        self.func = func
        self.name = func.__name__
        self.description = func.__doc__ or ""
        self.schema = self._generate_schema()

    def _generate_schema(self) -> dict:
        # 从函数签名生成 JSON Schema
        sig = inspect.signature(self.func)
        type_hints = get_type_hints(self.func)

        # 生成参数 schema
        parameters = {}
        required = []

        # 遍历函数参数，生成 JSON Schema
        for name, param in sig.parameters.items():
            # 忽略 self 参数
            if name == "self":
                continue

            # 获取参数类型和默认值
            annotation = type_hints.get(name, str)
            json_type = _TYPE_MAPPING.get(annotation, "string")

            # 生成参数 schema
            parameters[name] = {"type": json_type}

            # 如果参数没有默认值，则为必填参数
            if param.default is inspect.Parameter.empty:
                required.append(name)


        schema = {
            "type": "function", # 工具类型为函数
            "function": {
                "name": self.name,
                "description": self.description.strip(), # 工具描述，去除首尾空格
                "parameters": {
                    "type": "object",
                    "properties": parameters,
                    "required": required,
                },
            },
        }
        return schema

    @property # 获取工具的 JSON Schema
    def json_schema(self) -> dict:
        # 返回工具的 JSON Schema
        return self.schema

    async def invoke(self, **kwargs):
        # 调用工具函数
        # arguments: kwargs: 工具函数的参数
        # returns: str: 工具函数的返回值

        try:
            # 验证参数是否符合 JSON Schema
            params_schema = self.schema["function"]["parameters"]
            jsonschema.validate(instance=kwargs, schema=params_schema) 

            # 根据函数类型（同步或异步）调用工具函数
            if inspect.iscoroutinefunction(self.func):
                result = await self.func(**kwargs)
            else:
                result = self.func(**kwargs)

            # 处理工具函数的返回值
            if result is None:
                return ""
            elif isinstance(result, str):
                return result
            return str(result)
        
        except jsonschema.ValidationError as e:
            # 参数校验失败，给出精确的错误信息
            error_msg = f"参数校验失败: 字段 '{e.path[0]}' {e.message}" if e.path else f"参数校验失败: {e.message}"
            raise ToolExecutionError(self.name, error_msg) from e
        
        except Exception as e:
            # 函数执行出错
            raise ToolExecutionError(self.name, str(e)) from e

def tool(func):
    # 工具装饰器，将函数注册为工具
    # func: 工具函数
    # returns: Tool: 工具对象

    return Tool(func)

class ToolRegistry:
    # 工具注册表，管理所有注册的工具
    def __init__(self):
        self.tools: dict[str, Tool] = {}

    def register(self, tool_obj: Tool):
        # 注册工具对象
        # tool_obj: Tool: 工具对象
        self.tools[tool_obj.name] = tool_obj

    def get_tool(self, tool_name: str) -> Tool:
        # 获取工具对象
        # tool_name: str: 工具名称
        # returns: Tool: 工具对象
        # raises: ToolNotFoundError: 工具不存在

        if tool_name not in self.tools:
            raise ToolNotFoundError(tool_name)
        return self.tools[tool_name]

    def get_all_tools(self) -> list[Tool]:
        # 获取所有注册的工具对象
        # returns: list[Tool]: 工具对象列表
        return list(self.tools.values())

    def get_all_tools_schema(self) -> list[dict]:
        # 获取所有注册的工具的 JSON Schema
        # returns: list[dict]: 工具 JSON Schema 列表
        return [tool.json_schema for tool in self.get_all_tools()]

    async def execute_tool(self, tool_name: str, **kwargs) -> str:
        # 执行工具函数
        # tool_name: str: 工具名称
        # kwargs: 工具函数的参数
        # returns: str: 工具函数的返回值
        # raises: ToolNotFoundError: 工具不存在
        # raises: ToolExecutionError: 工具执行异常

        tool_obj = self.get_tool(tool_name)
        return await tool_obj.invoke(**kwargs)

    def __len__(self):
        # 获取注册的工具数量
        return len(self.tools)