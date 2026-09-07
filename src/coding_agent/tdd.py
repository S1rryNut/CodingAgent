# TDD 循环 Agent
# 在 CodingAgent 基础上，通过 system prompt 强制 TDD 流程：先写测试 → 跑测试（RED）→ 写实现 → 再跑测试（GREEN）→ 完成。

from .agent import CodingAgent

# TDD 流程指令
TDD_INSTRUCTIONS = """
========================================
【TDD 开发流程 - 必须严格遵守】
========================================

你必须按照测试驱动开发的流程完成任务：

第 1 步【写测试】：
- 先为需求编写测试文件（tests/ 目录下）
- 测试要覆盖正常情况和边界情况

第 2 步【跑测试，确认 RED】：
- 用 run_shell_command 运行 pytest
- 确认测试失败（因为实现还没写）
- 失败是正常的，证明测试有效

第 3 步【写实现】：
- 根据测试失败信息，编写最小实现
- 只写让测试通过需要的代码，不要过度设计

第 4 步【再跑测试，确认 GREEN】：
- 再次运行 pytest
- 如果还有失败，分析失败原因，修复实现，再跑
- 循环直到全部通过

第 5 步【收尾】：
- 所有测试通过后，检查代码质量
- 用 git status 确认改动
- 最后给出总结回答

【重要规则】
- 严禁在写测试之前先写实现
- 每次修改代码后都要重新跑测试
- 测试失败时要仔细阅读错误信息，不要盲目重试
========================================
"""

class TDDAgent(CodingAgent):
    # TDD 循环 Coding Agent
    # 继承 CodingAgent 的全部能力（工具、记忆、repo map），只在 system prompt 中追加 TDD 流程指令。
    
    def _build_system_prompt(self) -> str:
        # 在基础 system prompt 上追加 TDD 指令
        base_prompt = super()._build_system_prompt()
        return f"{base_prompt}\n\n{TDD_INSTRUCTIONS}"