"""测试工具系统：@tool 装饰器、JSON Schema 生成、ToolRegistry、工具执行"""

import asyncio
from coding_agent.tool import tool, Tool, ToolRegistry
from coding_agent.errors import ToolNotFoundError, ToolExecutionError


# ===== 测试用的工具函数 =====

@tool
def add(a: int, b: int) -> int:
    """两个数相加"""
    return a + b


@tool
def greet(name: str, greeting: str = "你好") -> str:
    """打招呼，可自定义问候语"""
    return f"{greeting}, {name}!"


@tool
async def async_double(x: int) -> int:
    """异步函数：把数字翻倍"""
    await asyncio.sleep(0.1)  # 模拟异步操作
    return x * 2


@tool
def bad_tool(x: int) -> int:
    """会抛异常的工具，测试错误处理"""
    raise ValueError("故意出错了")


async def main():
    # ===== 测试 1：@tool 装饰器 =====
    print("=== 测试 1：@tool 装饰器 ===")
    print(f"add 的类型: {type(add)}")
    print(f"add.name: {add.name}")
    print(f"add.description: {add.description}")
    print()

    # ===== 测试 2：JSON Schema 自动生成 =====
    print("=== 测试 2：JSON Schema 自动生成 ===")
    import json
    print("add 的 schema:")
    print(json.dumps(add.json_schema, indent=2, ensure_ascii=False))
    print()

    print("greet 的 schema（注意 greeting 有默认值，不是必填）:")
    print(json.dumps(greet.json_schema, indent=2, ensure_ascii=False))
    print()

    # 验证必填参数
    add_required = add.json_schema["function"]["parameters"]["required"]
    greet_required = greet.json_schema["function"]["parameters"]["required"]
    print(f"add 必填参数: {add_required}")
    print(f"greet 必填参数: {greet_required}（greeting 有默认值，所以不在必填里）")
    print()

    # ===== 测试 3：同步工具执行 =====
    print("=== 测试 3：同步工具执行 ===")
    result = await add.invoke(a=3, b=5)
    print(f"add(3, 5) = {result}")
    print(f"返回值类型: {type(result)}")  # 应该是 str
    print()

    # ===== 测试 4：异步工具执行 =====
    print("=== 测试 4：异步工具执行 ===")
    result = await async_double.invoke(x=21)
    print(f"async_double(21) = {result}")
    print()

    # ===== 测试 5：ToolRegistry =====
    print("=== 测试 5：ToolRegistry ===")
    registry = ToolRegistry()
    registry.register(add)
    registry.register(greet)
    registry.register(async_double)
    print(f"注册的工具数量: {len(registry)}")
    print(f"所有工具名: {[t.name for t in registry.get_all_tools()]}")
    print()

    # 获取所有 schema
    schemas = registry.get_all_tools_schema()
    print(f"schema 数量: {len(schemas)}")
    print()

    # 执行工具
    result = await registry.execute_tool("add", a=10, b=20)
    print(f"registry.execute_tool('add', a=10, b=20) = {result}")
    print()

    # ===== 测试 6：工具不存在 =====
    print("=== 测试 6：工具不存在 ===")
    try:
        registry.get_tool("not_exist")
    except ToolNotFoundError as e:
        print(f"捕获到 ToolNotFoundError: {e}")
    print()

    # ===== 测试 7：工具执行失败 =====
    print("=== 测试 7：工具执行失败 ===")
    registry.register(bad_tool)
    try:
        await registry.execute_tool("bad_tool", x=1)
    except ToolExecutionError as e:
        print(f"捕获到 ToolExecutionError: {e}")
        print(f"工具名: {e.tool_name}")
        print(f"错误信息: {e.message}")
    print()

    print("✅ 所有测试通过")


if __name__ == "__main__":
    asyncio.run(main())
