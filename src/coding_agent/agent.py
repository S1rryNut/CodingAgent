# Coding Agent 主控

from .llm import LLMClient
from .tool import ToolRegistry
from .errors import (
    MaxIterationsExceededError,
    ToolNotFoundError,
    ToolExecutionError,
)
from .memory.short_term import ShortTermMemory
from .memory.task_state import TaskState
from .memory.project_memory import ProjectMemory
from .repo_map import RepoMap
from .utils.json_parser import parse_json_robust

class CodingAgent:
    # 初始化 CodingAgent 类
    def __init__(
            self,
            llm_client: LLMClient,
            repo_path: str, 
            max_iterations: int = 20,  
        ):
        self.llm_client = llm_client
        self.repo_path = repo_path
        self.max_iterations = max_iterations

        # 初始化工具注册表、短期记忆、任务状态和项目记忆
        self.tool_registry = ToolRegistry()
        self._register_tools()

        self.short_term_memory = ShortTermMemory()
        self.task_state = TaskState()
        self.project_memory = ProjectMemory(repo_path)

        self.repo_map = RepoMap(repo_path)


    def _register_tools(self):
        # 注册工具到工具注册表
        from .tools.file_tools import read_file, write_file, edit_file, list_files
        from .tools.shell_tools import run_shell_command
        from .tools.code_search import grep_code, glob_files
        from .tools.git_tools import git_status, git_diff, git_commit

        tools = [
            read_file, write_file, edit_file, list_files,
            run_shell_command, 
            grep_code, glob_files,
            git_status, git_diff, git_commit,
        ]
        for tool in tools:
            self.tool_registry.register(tool)

    def _build_system_prompt(self) -> str:
        # 构建系统提示，包括代码库地图和项目记忆
        parts = [
            "你是一个专业的 Coding Agent，负责完成用户的编程任务。",
            "你可以读取、修改文件，执行命令，搜索代码，提交 Git。",
            "",
            "使用工具时注意：",
            "1. 每次只调用必要的工具，不要一次调用太多",
            "2. 工具返回错误时，阅读错误信息并修正后重试",
            "3. 完成任务后，直接给出总结回答，不要再调用工具",
        ]

        # 代码库地图
        repo_map_str = self.repo_map.build_map()
        if repo_map_str:
            parts.append(repo_map_str)

        # 项目记忆
        project_memory_str = self.project_memory.to_prompt()
        if project_memory_str:
            parts.append(project_memory_str)

        # 任务状态
        task_state_str = self.task_state.to_prompt()
        if task_state_str:
            parts.append(task_state_str)

        return "\n\n".join(parts)

    async def run(self, task: str) -> str:
    # 运行 CodingAgent，执行指定任务

        # 初始化任务状态
        self.task_state.set_goal(task)
        self.short_term_memory.add_message("user", task)

        print(f"===== 任务开始: {task[:50]}... =====")

        for iteration in range(self.max_iterations):
            print(f"===== 迭代 {iteration + 1}/{self.max_iterations} =====")

            # ===== 1. 组装消息 =====
            messages = [{
                "role": "system", 
                 "content": self._build_system_prompt()
            }]
            messages.extend(self.short_term_memory.get_messages())

            # ===== 2. 调用 LLM =====
            response = await self.llm_client.achat(
                messages, 
                tools = self.tool_registry.get_all_tools_schema(),
            )
            content = response["content"] or ""
            tool_calls = response.get("tool_calls")

            # 记录 assistant 消息
            self.short_term_memory.add_message(
                "assistant", 
                content, 
                tool_calls = tool_calls
            )

            # ===== 3. 有工具调用 → 执行工具 =====
            if tool_calls:
                for tc in tool_calls:
                    tool_name = tc["function"]["name"]
                    print(f"  调用工具: {tool_name}({tc['function']['arguments']})")

                    # 容错解析参数
                    try:
                        arguments = parse_json_robust(tc["function"]["arguments"])
                    except ValueError as e:
                        result = f"错误: 参数解析失败: {e}"
                    else:
                        # 执行工具
                        try:
                            result = await self.tool_registry.execute_tool(
                                tool_name, **arguments
                            )
                        except ToolNotFoundError as e:
                            result = f"错误: {e}"
                        except ToolExecutionError as e:
                            result = f"错误: {e}"

                    print(f"  工具结果: {result[:100]}...")

                    # 记录工具结果（必须带 tool_call_id）
                    self.short_term_memory.add_message(
                        "tool", result,
                        tool_call_id=tc["id"],
                    )

                    # 记录任务状态
                    self.task_state.add_step(tool_name, arguments, result)

                # 每轮结束检查是否需要压缩
                await self.short_term_memory.compress_if_needed(self.llm_client)
                self.task_state.increment_iteration()
                continue

            # ===== 4. 没有工具调用 = 最终回答 =====
            print("  (LLM 直接回答，任务结束)")
            return content

        # 超过最大迭代次数
        raise MaxIterationsExceededError(self.max_iterations)
