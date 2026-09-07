# 自定义异常类

class CodingAgentError(Exception):
    # 所有 Coding Agent 异常的基类
    pass

class ToolExecutionError(CodingAgentError):
    # 工具执行异常
    def __init__(self, tool_name: str, message: str):
        self.tool_name = tool_name
        self.message = message
        super().__init__(f"工具 '{tool_name}' 执行失败: {message}")

class ToolNotFoundError(CodingAgentError):
    # 工具未找到异常
    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        super().__init__(f"工具 '{tool_name}' 不存在")

class MaxIterationsExceededError(CodingAgentError):
    # 超过最大迭代次数异常
    def __init__(self, max_iterations: int):
        self.max_iterations = max_iterations
        super().__init__(f"超过最大迭代次数: {max_iterations},任务未完成")

class ConsecutiveToolExecutionError(CodingAgentError):
    # 连续工具执行失败异常
    def __init__(self, tool_name: str, consecutive_failures: int):
        self.tool_name = tool_name
        self.consecutive_failures = consecutive_failures
        super().__init__(f"工具 '{tool_name}' 连续执行失败 {consecutive_failures} 次，任务未完成")

class FileOperationError(CodingAgentError):
    # 文件操作异常
    def __init__(self, file_path: str, message: str):
        self.file_path = file_path
        self.message = message
        super().__init__(f"文件操作失败 '{file_path}': {message}")

class CommandExecutionError(CodingAgentError):
    # 命令执行异常
    def __init__(self, command: str, message: str):
        self.command = command
        self.message = message
        super().__init__(f"命令 '{command}' 执行失败: {message}")

class CommandTimeoutError(CodingAgentError):
    """命令执行超时"""
    def __init__(self, command: str, timeout: int):
        self.command = command
        self.timeout = timeout
        super().__init__(f"命令执行超时 ({timeout}s): {command}")


class EditConflictError(CodingAgentError):
    # 编辑冲突异常
    # 当在文件中搜索文本时，如果没有找到匹配的文本，或者找到了多个匹配的文本，就会抛出此异常。
    def __init__(self, file_path: str, search_text: str, matches: int):
        self.file_path = file_path
        self.search_text = search_text
        self.matches = matches
        if matches == 0:
            super().__init__(f"文件 '{file_path}' 中未找到匹配的文本: '{search_text}'")
        else:
            super().__init__(f"文件 '{file_path}' 中找到多个匹配的文本: '{search_text}'，匹配数量: {matches}")