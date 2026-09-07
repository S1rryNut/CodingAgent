"""测试 LLM 客户端：纯对话 + Function Calling"""

import asyncio
import os
from dotenv import load_dotenv

# 加载 .env
load_dotenv()

from coding_agent.llm import LLMClient


async def main():
    # 用 DeepSeek 测试
    llm = LLMClient(
    model="qwen-plus",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    # ===== 测试 1：纯对话 =====
    print("=== 测试 1：纯对话 ===")
    messages = [
        {"role": "system", "content": "你是一个简洁的助手"},
        {"role": "user", "content": "1+1等于几？只回答数字"},
    ]
    result = await llm.achat(messages)
    print(f"回答: {result['content']}")
    print(f"finish_reason: {result['finish_reason']}")
    print(f"token 用量: {result['usage']}")
    print()

    # ===== 测试 2：Function Calling =====
    print("=== 测试 2：Function Calling ===")
    tools = [
        {
            "type": "function",
            "function": {
                "name": "calculator",
                "description": "计算数学表达式",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "数学表达式，如 '123 * 456'",
                        }
                    },
                    "required": ["expression"],
                },
            },
        }
    ]
    messages = [
        {"role": "system", "content": "你是一个助手，可以使用 calculator 工具"},
        {"role": "user", "content": "帮我算一下 12345 乘以 67890"},
    ]
    result = await llm.achat(messages, tools=tools)
    print(f"content: {result['content']}")
    print(f"tool_calls: {result['tool_calls']}")
    print(f"finish_reason: {result['finish_reason']}")
    print()

    if result["tool_calls"]:
        tc = result["tool_calls"][0]
        print(f"  工具名: {tc['name']}")
        print(f"  参数: {tc['arguments']}")
        print(f"  调用ID: {tc['id']}")
    else:
        print("  ⚠️ 没有返回工具调用，LLM 可能直接回答了")

    print("\n✅ 测试完成")


if __name__ == "__main__":
    asyncio.run(main())
