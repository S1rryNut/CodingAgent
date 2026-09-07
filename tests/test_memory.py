"""测试记忆系统：ShortTermMemory、TaskState、ProjectMemory"""

import asyncio
import tempfile
import json
from pathlib import Path

from coding_agent.memory.short_term import ShortTermMemory
from coding_agent.memory.task_state import TaskState
from coding_agent.memory.project_memory import ProjectMemory


# ===== 假的 LLM 客户端，不调用真实 API =====
class FakeLLMClient:
    """模拟 LLM 客户端，直接返回写死的摘要"""

    async def achat(self, messages, tools=None, temperature=0.7, max_tokens=None):
        return {
            "content": "用户要求实现命令行计算器，已完成需求分析和代码编写，当前在做测试。",
            "tool_calls": None,
            "finish_reason": "stop",
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        }


def test_short_term_memory():
    print("=== 测试 ShortTermMemory ===")

    memory = ShortTermMemory(token_budget=50, compression_ratio=0.5)
    print(f"token_budget: {memory.token_budget}")
    print(f"compression_ratio: {memory.compression_ratio}")
    print(f"初始消息数: {len(memory)}")

    # 添加消息
    memory.add_message("system", "你是一个编程助手")
    memory.add_message("user", "帮我实现一个计算器")
    memory.add_message("assistant", "好的，我来实现", tool_calls=[{"id": "call_1", "name": "read_file", "arguments": "{}"}])
    memory.add_message("tool", "文件内容...", tool_call_id="call_1")

    print(f"添加 4 条消息后: {len(memory)}")
    messages = memory.get_messages()
    print(f"get_messages 返回: {len(messages)} 条")
    print(f"第 3 条消息: {messages[2]}")
    print(f"第 4 条消息: {messages[3]}")
    print(f"token 数量: {memory.get_token_count()}")

    # 测试压缩（用 fake LLM）
    print("\n-- 测试压缩 --")
    memory = ShortTermMemory(token_budget=50, compression_ratio=0.5)
    for i in range(20):
        memory.add_message("user", f"这是第 {i} 条很长的测试消息，内容是用来撑大 token 数量的" * 5)

    print(f"压缩前消息数: {len(memory)}, token 数: {memory.get_token_count()}")
    compressed = asyncio.run(memory.compress_if_needed(FakeLLMClient()))
    print(f"是否触发压缩: {compressed}")
    print(f"压缩后消息数: {len(memory)}, token 数: {memory.get_token_count()}")
    print(f"摘要缓存: {memory._summary_cache[:50]}...")

    # 压缩后 get_messages 应该包含摘要
    messages = memory.get_messages()
    print(f"压缩后 get_messages 返回: {len(messages)} 条（第一条应该是摘要）")
    print(f"第一条: {messages[0]['role']}: {messages[0]['content'][:40]}...")

    # clear
    memory.clear()
    print(f"clear 后消息数: {len(memory)}, 摘要: {memory._summary_cache}")
    print()


def test_task_state():
    print("=== 测试 TaskState ===")

    state = TaskState(max_steps=3)
    print(f"初始 goal: {state.goal}")

    # set_goal
    state.set_goal("实现一个命令行计算器")
    print(f"设置 goal 后: {state.goal}")
    print(f"start_time: {state.start_time}")
    print(f"iterations: {state.iterations}")

    # add_step
    state.add_step("read_file", {"filename": "design.md"}, "设计文档内容...")
    state.add_step("write_file", {"filename": "calc.py"}, "已写入: calc.py (1200 字符)")
    state.add_step("run_command", {"command": "python calc.py 5 + 3"}, "8")
    state.add_step("run_command", {"command": "python calc.py 10 / 4"}, "2.5")

    print(f"steps 数量: {len(state.steps)}（超过 max_steps=3 应只保留 3 条）")
    print(f"last_tool_result: {state.last_tool_result}")

    # increment_iteration
    state.increment_iteration()
    state.increment_iteration()
    print(f"迭代 2 次后 iterations: {state.iterations}")

    # add_constraint
    state.add_constraint("使用 Python 标准库")
    state.add_constraint("使用 Python 标准库")  # 重复，不应添加
    print(f"constraints: {state.constraints}")

    # to_prompt
    print("\n-- to_prompt 输出 --")
    print(state.to_prompt())

    # summary
    summary = state.summary()
    print(f"\nsummary 类型: {type(summary)}")
    print(f"summary: {summary}")

    # reset
    state.reset()
    print(f"\nreset 后 goal: {state.goal}")
    print(f"reset 后 steps: {len(state.steps)}")
    print()

    # to_prompt 在无 goal 时
    print(f"无 goal 时 to_prompt: {state.to_prompt()}")
    print()


def test_project_memory():
    print("=== 测试 ProjectMemory ===")

    # 用临时目录测试，避免污染项目
    with tempfile.TemporaryDirectory() as tmp_dir:
        pm = ProjectMemory(tmp_dir)
        print(f"记忆文件路径: {pm.memory_file}")

        # 添加内容
        pm.add_tech_stack("Python 3.13")
        pm.add_tech_stack("FastAPI")
        pm.add_tech_stack("Python 3.13")  # 重复，不应添加
        pm.add_convention("函数用 snake_case")
        pm.add_lesson("任务完成前先跑测试")
        pm.add_common_issue("导入失败", "检查 PYTHONPATH")
        pm.add_common_issue("导入失败", "检查 PYTHONPATH")  # 重复，不应添加
        pm.set_custom("owner", "S1rryNut")

        print(f"tech_stack: {pm.data['tech_stack']}")
        print(f"conventions: {pm.data['conventions']}")
        print(f"lessons: {pm.data['lessons']}")
        print(f"common_issues: {pm.data['common_issues']}")
        print(f"get_custom('owner'): {pm.get_custom('owner')}")
        print(f"get_custom('不存在', '默认值'): {pm.get_custom('不存在', '默认值')}")
        print(f"has_content: {pm.has_content()}")

        # to_prompt
        print("\n-- to_prompt 输出 --")
        print(pm.to_prompt())

        # 持久化测试：重新加载，验证数据还在
        print("\n-- 持久化测试 --")
        pm2 = ProjectMemory(tmp_dir)
        print(f"重新加载后 tech_stack: {pm2.data['tech_stack']}")
        print(f"重新加载后 common_issues: {pm2.data['common_issues']}")
        print(f"重新加载后 custom: {pm2.data['custom']}")
        print(f"重新加载后 has_content: {pm2.has_content()}")

        # clear
        pm2.clear()
        print(f"\nclear 后 has_content: {pm2.has_content()}")
        print(f"clear 后 data: {pm2.data}")
    print()


if __name__ == "__main__":
    test_short_term_memory()
    test_task_state()
    test_project_memory()
    print("✅ 所有记忆模块测试完成")
