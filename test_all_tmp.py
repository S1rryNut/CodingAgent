"""全模块综合测试

覆盖：工具系统、file_tools、shell_tools、code_search、git_tools、
RepoMap、CodingAgent 主循环（用 fake LLM，不调真实 API）。
"""

import asyncio
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from coding_agent.tool import ToolRegistry
from coding_agent.tools.file_tools import read_file, write_file, edit_file, list_files
from coding_agent.tools.shell_tools import run_shell_command
from coding_agent.tools.code_search import grep_code, glob_files
from coding_agent.tools.git_tools import git_status, git_diff, git_commit
from coding_agent.repo_map import RepoMap
from coding_agent.agent import CodingAgent


# ============================================================
# 测试 1：file_tools
# ============================================================
def test_file_tools(tmp_dir: Path):
    print("=== 测试 file_tools ===")

    # write_file
    result = write_file.func(
        filename=str(tmp_dir / "calc.py"),
        content="def add(a, b):\n    return a + b\n\ndef sub(a, b):\n    return a - b\n",
    )
    print(f"write_file: {result}")

    # 自动创建子目录
    result = write_file.func(
        filename=str(tmp_dir / "src" / "core.py"),
        content="x = 1\n",
    )
    print(f"write_file(子目录): {result}")

    # read_file
    result = read_file.func(filename=str(tmp_dir / "calc.py"))
    print(f"read_file:\n{result}")

    # read_file 带 offset/limit
    result = read_file.func(filename=str(tmp_dir / "calc.py"), offset=1, limit=2)
    print(f"read_file(offset=1, limit=2):\n{result}")

    # edit_file
    result = edit_file.func(
        filename=str(tmp_dir / "calc.py"),
        search_text="def add(a, b):",
        new_text="def add(a: int, b: int) -> int:",
    )
    print(f"edit_file: {result}")

    # edit_file 找不到
    result = edit_file.func(
        filename=str(tmp_dir / "calc.py"),
        search_text="不存在的文本",
        new_text="xxx",
    )
    print(f"edit_file(找不到): {result}")

    # list_files
    result = list_files.func(directory=str(tmp_dir))
    print(f"list_files:\n{result}")

    # 错误场景
    print(f"read_file(不存在): {read_file.func(filename=str(tmp_dir / 'nope.py'))}")
    print(f"list_files(不存在): {list_files.func(directory=str(tmp_dir / 'nope'))}")
    print()


# ============================================================
# 测试 2：shell_tools
# ============================================================
def test_shell_tools(tmp_dir: Path):
    print("=== 测试 shell_tools ===")

    # 正常命令
    result = run_shell_command.func(command="echo hello", cwd=str(tmp_dir))
    print(f"echo: {result}")

    # 失败命令（退出码非 0）
    result = run_shell_command.func(command="python -c \"raise ValueError('boom')\"", cwd=str(tmp_dir))
    print(f"失败命令:\n{result}")

    # 不存在的命令
    result = run_shell_command.func(command="definitely_not_a_command_xyz", cwd=str(tmp_dir))
    print(f"不存在的命令:\n{result}")
    print()


# ============================================================
# 测试 3：code_search
# ============================================================
def test_code_search(tmp_dir: Path):
    print("=== 测试 code_search ===")

    # grep_code
    result = grep_code.func(pattern="def add", directory=str(tmp_dir))
    print(f"grep 'def add':\n{result}")

    # grep 正则
    result = grep_code.func(pattern=r"def \w+", directory=str(tmp_dir))
    print(f"grep 正则:\n{result}")

    # glob_files
    result = glob_files.func(pattern="**/*.py", directory=str(tmp_dir))
    print(f"glob **/*.py:\n{result}")

    # 无效正则
    result = grep_code.func(pattern="[", directory=str(tmp_dir))
    print(f"无效正则: {result}")
    print()


# ============================================================
# 测试 4：git_tools（在临时 git 仓库里）
# ============================================================
def test_git_tools(tmp_dir: Path):
    print("=== 测试 git_tools ===")

    # 初始化 git 仓库
    subprocess.run(["git", "init"], cwd=str(tmp_dir), capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=str(tmp_dir), capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=str(tmp_dir), capture_output=True)

    # 创建文件并提交
    write_file.func(filename=str(tmp_dir / "a.py"), content="x = 1\n")
    subprocess.run(["git", "add", "-A"], cwd=str(tmp_dir), capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=str(tmp_dir), capture_output=True)

    # 修改文件（未提交）
    write_file.func(filename=str(tmp_dir / "a.py"), content="x = 2\n")

    # git_status
    result = git_status.func(directory=str(tmp_dir))
    print(f"git_status:\n{result}")

    # git_diff
    result = git_diff.func(directory=str(tmp_dir))
    print(f"git_diff:\n{result}")

    # git_diff 指定文件
    result = git_diff.func(filename="a.py", directory=str(tmp_dir))
    print(f"git_diff(a.py):\n{result}")

    # git_commit
    result = git_commit.func(message="update a.py", directory=str(tmp_dir))
    print(f"git_commit:\n{result}")

    # commit 后再看 status
    result = git_status.func(directory=str(tmp_dir))
    print(f"commit 后 git_status:\n{result}")
    print()


# ============================================================
# 测试 5：RepoMap
# ============================================================
def test_repo_map(tmp_dir: Path):
    print("=== 测试 RepoMap ===")

    # 创建几个文件
    write_file.func(filename=str(tmp_dir / "main.py"), content="""import sys

def main():
    print("hello")

if __name__ == "__main__":
    main()
""")
    write_file.func(filename=str(tmp_dir / "src" / "calculator.py"), content="""from decimal import Decimal

class Calculator:
    def add(self, a, b):
        return a + b

    def divide(self, a, b):
        if b == 0:
            raise ValueError("div by zero")
        return a / b

def helper():
    return 42
""")
    write_file.func(filename=str(tmp_dir / "tests" / "test_calculator.py"), content="""from src.calculator import Calculator

def test_add():
    assert Calculator().add(1, 2) == 3
""")

    # 构建地图
    repo_map = RepoMap(str(tmp_dir), token_budget=3000)
    result = repo_map.build_map()
    print(result)
    print()


# ============================================================
# 测试 6：CodingAgent 主循环（fake LLM）
# ============================================================
class FakeLLM:
    """模拟 LLM：第一轮调用工具，第二轮直接回答"""

    def __init__(self):
        self.calls = 0

    async def achat(self, messages, tools=None, temperature=0.7, max_tokens=None):
        self.calls += 1
        if self.calls == 1:
            # 第一轮：返回工具调用（list_files）
            return {
                "content": "让我先看看目录里有什么。",
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {"name": "list_files", "arguments": "{}"},
                    }
                ],
                "finish_reason": "tool_calls",
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            }
        # 第二轮：直接回答
        return {
            "content": "目录结构已查看，任务完成。",
            "tool_calls": None,
            "finish_reason": "stop",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }


def test_agent_loop(tmp_dir: Path):
    print("=== 测试 CodingAgent 主循环 ===")

    # 在临时目录创建一点内容
    write_file.func(filename=str(tmp_dir / "README.md"), content="# Test Project\n")

    # 切到临时目录，模拟"在项目目录运行"的真实场景
    old_cwd = Path.cwd()
    os.chdir(tmp_dir)
    try:
        fake_llm = FakeLLM()
        agent = CodingAgent(llm_client=fake_llm, repo_path=str(tmp_dir), max_iterations=5)

        result = asyncio.run(agent.run("看看这个项目里有什么"))
    finally:
        os.chdir(old_cwd)  # 恢复原目录

    print(f"最终回答: {result}")
    print(f"LLM 调用次数: {fake_llm.calls}（应为 2）")
    print(f"短期记忆消息数: {len(agent.short_term_memory)}（应为 4: user + assistant + tool + assistant）")
    print(f"任务状态步骤数: {len(agent.task_state.steps)}（应为 1: list_files）")
    print(f"任务状态迭代数: {agent.task_state.iterations}（应为 1）")

    # 验证记忆内容：正确序列是 user → assistant(带tool_calls) → tool → assistant(最终回答)
    messages = agent.short_term_memory.get_messages()
    roles = [m["role"] for m in messages]
    print(f"消息角色序列: {roles}")
    assert roles == ["user", "assistant", "tool", "assistant"], f"消息序列不对: {roles}"

    # 验证 assistant 第一条带 tool_calls
    assert messages[1]["tool_calls"] is not None, "第一条 assistant 消息缺少 tool_calls"
    print(f"assistant 第一条的 tool_calls: {messages[1]['tool_calls'][0]['function']['name']}")

    # 验证 tool 消息带 tool_call_id
    tool_msg = messages[2]
    assert "tool_call_id" in tool_msg, "tool 消息缺少 tool_call_id"
    assert tool_msg["tool_call_id"] == "call_1", "tool_call_id 与 assistant 的调用 ID 不对应"
    print(f"tool 消息的 tool_call_id: {tool_msg['tool_call_id']}")

    # 验证工具结果内容
    assert "README.md" in tool_msg["content"], f"工具结果里应该有 README.md: {tool_msg['content']}"
    print(f"工具结果包含 README.md: ✅")

    # 验证任务状态
    assert len(agent.task_state.steps) == 1
    assert agent.task_state.steps[0]["tool"] == "list_files"
    assert agent.task_state.steps[0]["iterations"] == 0
    print(f"任务状态记录的工具: {agent.task_state.steps[0]['tool']}")

    # 验证最终回答
    assert result == "目录结构已查看，任务完成。", f"最终回答不对: {result}"

    print("✅ Agent 主循环测试通过")
    print()


# ============================================================
# 主入口
# ============================================================
if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        test_file_tools(tmp_dir)
        test_shell_tools(tmp_dir)
        test_code_search(tmp_dir)
        test_git_tools(tmp_dir)
        test_repo_map(tmp_dir)
        test_agent_loop(tmp_dir)

    print("🎉 所有模块测试完成")
