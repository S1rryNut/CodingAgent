# 任务状态类，用于记录和管理任务的目标、步骤、约束条件等信息
import json
from datetime import datetime

class TaskState:
    # 任务状态类

    def __init__(self, max_steps: int = 20):
        # 初始化任务状态
        self.goal: str | None = None # 任务目标
        self.steps: list[dict] = [] # 任务步骤列表
        self.last_tool_result: str | None = None # 上一次工具调用结果
        self.constraints: list[str] = [] # 任务约束条件
        self.max_steps: int = max_steps # 最大步骤数
        self.iterations: int = 0 # 任务迭代次数
        self.start_time: str | None = None # 任务开始时间

    def set_goal(self, goal: str):
        # 设置任务目标
        self.goal = goal
        self.start_time = datetime.now().strftime("%H:%M:%S") # 设置任务开始时间
        self.iterations = 0 # 重置迭代次数

    def add_step(self, tool_name: str, arguments: dict, result: str):
        # 添加任务步骤
        result_short = result[:200] + "..." if len(result) > 200 else result

        # 构造步骤字典
        step = {
            "iterations": self.iterations,
            "tool": tool_name,
            "args":json.dumps(arguments, ensure_ascii=False)[:1000],  # 截断参数，避免过长
            "result": result_short,
        }
        self.steps.append(step)
        self.last_tool_result = result_short

        # 如果步骤数量超过最大值，保留最近的 max_steps 步骤
        if len(self.steps) > self.max_steps:
            self.steps = self.steps[-self.max_steps:]  # 保留最近的 max_steps 步骤

    def increment_iteration(self):
        # 增加任务迭代次数
        self.iterations += 1

    def add_constraint(self, constraint: str):
        # 添加任务约束条件
        if constraint not in self.constraints:
            self.constraints.append(constraint)

    def to_prompt(self) -> str:
        # 将任务状态转换为提示字符串，用于 LLM 输入
        if not self.goal:
            return "任务目标未设置。"

        # 构建任务状态提示字符串
        lines = [
            "=== 当前任务状态 ===",
            f"目标：{self.goal}",
            f"迭代次数：{self.iterations}",
        ]

        # 添加约束条件和已执行步骤信息
        if self.constraints:
            lines.append("约束：")
            for constraint in self.constraints:
                lines.append(f"  - {constraint}")

        if self.steps:
            lines.append("已执行步骤：")
            for step in self.steps[-10:]:  # 只显示最近的10个步骤
                lines.append(
                    f"  [{step['iterations']}] {step['tool']}("
                    f"{step['args']}) → {step['result'][:50]}"
                )
        if self.last_tool_result:
            lines.append(f"上一次工具调用结果：{self.last_tool_result[:50]}")

        lines.append("====================")
        return "\n".join(lines)
    def reset(self):
        # 重置任务状态
        self.goal = None
        self.steps = []
        self.last_tool_result = None
        self.constraints = []
        self.iterations = 0
        self.start_time = None

    def summary(self) -> dict:
        # 返回任务状态的简要摘要
        return {
            "goal": self.goal,
            "iteration": self.iterations,
            "steps_count": len(self.steps),
            "constraints": self.constraints,
            "start_time": self.start_time,
        }
    
