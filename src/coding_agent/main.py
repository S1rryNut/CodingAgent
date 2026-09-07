# Coding Agent 命令行入口
# python -m coding_agent.main "你的任务描述"
# python -m coding_agent.main --tdd "你的任务描述"

import asyncio
import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from .llm import LLMClient
from .agent import CodingAgent
from .tdd import TDDAgent

def get_llm_client() -> LLMClient:
    # 加载 .env 文件 从环境变量创建 LLM 客户端 
    load_dotenv()

    # 支持 DEEPSEEK 或 DASHSCOPE
    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
    base_url = os.getenv("DEEPSEEK_BASE_URL") or "https://api.deepseek.com"
    model = os.getenv("DEEPSEEK_MODEL") or "deepseek-chat"

    if not api_key:
        raise ValueError("未找到 API Key，请在 .env 中配置 DEEPSEEK_API_KEY 或 DASHSCOPE_API_KEY")

    return LLMClient(
        model=model,
        api_key=api_key,
        base_url=base_url,
    )

async def main():
    parser = argparse.ArgumentParser(description="Coding Agent")
    parser.add_argument("task", nargs="?", help="任务描述")
    parser.add_argument("--tdd", action="store_true", help="使用 TDD 模式")
    parser.add_argument("--repo", default=".", help="项目目录（默认当前目录）")
    args = parser.parse_args()

    # 交互模式：没有任务参数时，循环读输入
    if not args.task:
        print("Coding Agent 交互模式，输入任务，输入 exit 退出")
        while True:
            task = input("\n> ")
            if task.lower() in ("exit", "quit"):
                break
            if not task.strip():
                continue
            await run_task(task, args)
    else:
        await run_task(args.task, args)

async def run_task(task: str, args):
    llm = get_llm_client()

    if args.tdd:
        agent = TDDAgent(llm_client=llm, repo_path=args.repo)
        print("【TDD 模式】")
    else:
        agent = CodingAgent(llm_client=llm, repo_path=args.repo)

    try:
        result = await agent.run(task)
        print(f"\n===== 最终回答 =====\n{result}")
    except Exception as e:
        print(f"\n任务失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())



