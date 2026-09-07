# 文件操作工具
# 提供 read_file、write_file、edit_file、list_files 四个工具，让 Agent 能读写修改项目文件。

from pathlib import Path
from ..tool import tool

@tool
def read_file(filename: str, offset: int = 0, limit: int = 2000) -> str:
    # 读取文件内容

    try:
        path = Path(filename)
        if not path.is_file():
            return f"错误: 文件 '{filename}' 不存在"

        # 读取文件内容
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 处理 offset 和 limit
        selected_lines = lines[offset:offset + limit]

        # 将选中的行转换为字符串
        result = []
        for i, line in enumerate(selected_lines, start=offset + 1):
            result.append(f"{i:4d}: {line.rstrip()}")  # 添加行号

        # 如果有更多行未显示，提示用户
        total_lines = len(lines)
        if offset + limit < total_lines:
            result.append(f"... (共 {total_lines} 行，已显示 {offset + 1}-{offset + len(selected_lines)} 行)")

        return "\n".join(result)

    # 处理文件读取异常
    except FileNotFoundError:
        return f"错误: 文件 '{filename}' 不存在"
    except PermissionError:
        return f"错误: 没有权限读取 '{filename}'"
    except UnicodeDecodeError:
        return f"错误: '{filename}' 不是文本文件或编码不是 UTF-8"
    except Exception as e:
        return f"错误: 读取 '{filename}' 失败: {e}"
    
    
@tool
def write_file(filename: str, content: str) -> str:
    # 写入内容到文件，如果文件不存在则创建
    try:
        path = Path(filename)
        # 确保父目录存在
        path.parent.mkdir(parents=True, exist_ok=True)

        # 写入内容到文件
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        char_count = len(content)
        return f"成功: 已写入 {char_count} 个字符到 '{filename}'"
    except Exception as e:
        return f"错误: 写入 '{filename}' 失败: {e}"


@tool
def edit_file(filename: str, search_text: str, new_text: str) -> str:
    # 编辑文件内容，替换指定文本
    try:
        path = Path(filename)
        if not path.is_file():
            return f"错误: 文件 '{filename}' 不存在"

        # 读取文件内容
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # 查找匹配的文本
        matches = content.count(search_text)
        if matches == 0:
            return f"错误: 在 '{filename}' 中未找到: '{search_text[:50]}'"
        elif matches > 1:
            return f"错误: '{search_text[:50]}' 在 '{filename}' 中匹配了 {matches} 次，请提供更多上下文"

        # 替换文本
        new_content = content.replace(search_text, new_text)

        # 写回文件
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)

        return f"成功: 已将 '{search_text}' 替换为 '{new_text}'"

    except FileNotFoundError:
        return f"错误: 文件 '{filename}' 不存在"
    except PermissionError:
        return f"错误: 没有权限编辑 '{filename}'"
    except UnicodeDecodeError:
        return f"错误: '{filename}' 不是文本文件或编码不是 UTF-8"
    except Exception as e:
        return f"错误: 编辑 '{filename}' 失败: {e}"


@tool
def list_files(directory: str = ".") -> str:
    # 列出指定目录下的所有文件和子目录
    try:
        path = Path(directory)
        if not path.exists():
            return f"错误: 目录 '{directory}' 不存在"
        if not path.is_dir():
            return f"错误: '{directory}' 不是目录"

        # 获取目录下的所有文件和子目录
        items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))

        # 构建输出结果
        result = []
        for item in items:
            if item.is_dir():
                result.append(f"[目录]  {item.name}")
            else:
                size = item.stat().st_size
                result.append(f"[文件] {item.name} ({size} 字节)")

        return "\n".join(result) if result else f"目录 '{directory}' 为空"

    except FileNotFoundError:
        return f"错误: 目录 '{directory}' 不存在"
    except PermissionError:
        return f"错误: 没有权限访问 '{directory}'"
    except Exception as e:
        return f"错误: 列出目录 '{directory}' 失败: {e}"