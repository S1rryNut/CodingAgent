# 代码搜索工具

import re
from pathlib import Path

from ..tool import tool

# 默认排除的目录
DEFAULT_EXCLUDE = {".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build", ".coding_agent"}

@tool
def grep_code(pattern: str, file_pattern: str = "*.py", directory: str = ".", max_results: int = 50) -> str:
    # 在指定目录下搜索匹配的代码行，支持文件名模式过滤
    # pattern: 要搜索的正则表达式模式
    # file_pattern: 文件名模式，例如 "*.py"
    # directory: 搜索的根目录，默认为当前目录
    # max_results: 最大返回结果数，默认为 50
    try:
        root_path = Path(directory)
        if not root_path.exists():
            return f"错误: 目录 '{directory}' 不存在"
        if not root_path.is_dir():
            return f"错误: '{directory}' 不是目录"
        
        # 搜索匹配的代码行
        try:
            regex = re.compile(pattern)
        except re.error as e:
            return f"错误: 无效的正则表达式 '{pattern}': {e}"

        # 搜索文件并收集匹配结果
        matches = []
        for file_path in root_path.rglob(file_pattern):
            # 排除默认排除的目录
            if any(excluded in file_path.parts for excluded in DEFAULT_EXCLUDE):
                continue
            if not file_path.is_file():
                continue

            # 读取文件内容并搜索匹配的行
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    for line_number, line in enumerate(f, start=1):
                        if regex.search(line):
                            matches.append(f"{file_path}:{line_number}: {line.rstrip()[:200]}") # 限制每行输出长度为 200 个字符
                            if len(matches) >= max_results:
                                break
            except (IOError, UnicodeDecodeError): # 处理文件读取错误
                continue

            if len(matches) >= max_results:
                break

        if not matches:
            return f"未找到匹配 '{pattern}' 的内容（文件类型: {file_pattern}）"

        result = f"找到 {len(matches)} 处匹配:\n" + "\n".join(matches)
        if len(matches) >= max_results:
            result += f"\n... (结果已截断，仅显示前 {max_results} 条)"

        return result

    except Exception as e:
        return f"错误: 搜索过程中发生异常: {e}"


@tool
def glob_files(pattern: str, directory: str = ".") -> str:
    # 列出指定目录下匹配文件名模式的所有文件
    # pattern: 文件名模式，例如 "*.py"
    # directory: 搜索的根目录，默认为当前目录
    try:
        root_path = Path(directory)
        if not root_path.exists():
            return f"错误: 目录 '{directory}' 不存在"
        if not root_path.is_dir():
            return f"错误: '{directory}' 不是目录"

        # 搜索匹配的文件
        matched_files = []
        for file_path in root_path.glob(pattern):
            # 排除默认排除的目录
            if any(excluded in file_path.parts for excluded in DEFAULT_EXCLUDE):
                continue
            if file_path.is_file():
                matched_files.append(str(file_path))

        if not matched_files:
            return f"未找到匹配 '{pattern}' 的文件"

        if len(matched_files) > 100:
            shown_files = matched_files[:100]
            return "\n".join(shown_files) + f"\n... (共 {len(matched_files)} 个文件，仅显示前 100 个)"
        return "\n".join(matched_files)
    
    except Exception as e:
        return f"错误: 搜索失败: {e}"