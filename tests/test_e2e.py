"""端到端真实测试：用真实 LLM API 跑 TDDAgent

任务：实现 is_even 函数（TDD 流程）
验证：写测试 → RED → 写实现 → GREEN → 总结
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
from coding_agent.llm import LLMClient
from coding_agent.tdd import TDDAgent


# CodingAgent 虚拟环境里的 python（pytest 装在这里面）
VENV_PYTHON = r"C:\Users\1\Desktop\Cls\CodingAgent\.venv\Scripts\python.exe"


async def main():
    load_dotenv()

    # 配置 LLM：优先 DeepSeek，失败提示切换 DashScope
    api_key = os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    if not api_key:
        # 降级到 DashScope
        api_key = os.getenv("DASHSCOPE_API_KEY")
        base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        model = "qwen-plus"
        print("使用 DashScope (qwen-plus)")

    if not api_key:
        print("错误: 未找到任何 API Key")
        return

    llm = LLMClient(model=model, api_key=api_key, base_url=base_url)

    # 在临时目录跑任务（手动管理：先切回原目录再删除，避免 Windows 占用）
    import shutil
    old_cwd = Path.cwd()
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        os.chdir(tmp_dir)  # 模拟"在项目目录运行"

        agent = TDDAgent(llm_client=llm, repo_path=str(tmp_dir), max_iterations=30)

        task = f"""
        实现一个函数 is_even(n)，判断整数 n 是否为偶数。

        请严格按 TDD 流程：
        1. 先写测试文件 tests/test_is_even.py，覆盖 is_even(2) 为 True、is_even(3) 为 False、is_even(0) 为 True
        2. 运行测试，确认失败（RED）
        3. 写实现文件 is_even.py
        4. 再运行测试，确认全部通过（GREEN）
        5. 总结

        运行测试的命令请使用: {VENV_PYTHON} -m pytest tests/ -v
        """

        try:
            result = await agent.run(task)
            print(f"\n===== 最终回答 =====\n{result}")
        except Exception as e:
            print(f"\n任务失败: {type(e).__name__}: {e}")

        # 验证产物
        print("\n===== 产物检查 =====")
        test_file = tmp_dir / "tests" / "test_is_even.py"
        impl_file = tmp_dir / "is_even.py"
        print(f"测试文件存在: {test_file.exists()}")
        print(f"实现文件存在: {impl_file.exists()}")
        if impl_file.exists():
            print(f"is_even.py 内容:\n{impl_file.read_text(encoding='utf-8')}")

        # 直接验证实现正确性
        if impl_file.exists():
            sys.path.insert(0, str(tmp_dir))
            try:
                from is_even import is_even
                checks = [
                    (is_even(2), True, "is_even(2)"),
                    (is_even(3), False, "is_even(3)"),
                    (is_even(0), True, "is_even(0)"),
                ]
                for got, want, name in checks:
                    status = "✅" if got == want else "❌"
                    print(f"{status} {name} = {got} (期望 {want})")
            except ImportError as e:
                print(f"❌ 无法导入 is_even: {e}")
    finally:
        os.chdir(old_cwd)  # 先切回原目录
        shutil.rmtree(tmp_dir, ignore_errors=True)  # 再删除临时目录


if __name__ == "__main__":
    asyncio.run(main())
