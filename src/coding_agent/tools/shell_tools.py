# Shell 命令工具

import subprocess
from ..tool import tool

@tool
def run_shell_command(command: str, cwd: str = ".", timeout: int = 30) -> str:
    # 执行 shell 命令并返回结果
    # command: str: 要执行的 shell 命令
    # cwd: str: 命令执行的工作目录，默认为当前目录
    # timeout: int: 命令执行超时时间，单位为秒，默认为 30 秒
    # return: str: 命令执行结果

    try:
        result = subprocess.run(
            command,
            shell=True, # 使用 shell 执行命令
            cwd=cwd,
            capture_output=True, # 捕获标准输出和标准错误
            text=True, # 将输出解码为字符串
            encoding="utf-8", # 使用 UTF-8 编码
            errors="replace", # 无法解码的字符用替换符
            timeout=timeout, # 设置超时时间
        )
        # 组装输出结果
        parts = []
        if result.stdout:
            parts.append(f"[stdout]\n{result.stdout}")
        if result.stderr:
            parts.append(f"[stderr]\n{result.stderr}")

        output = "\n".join(parts) if parts else "(无输出)"

        # 如果输出过长，截断输出，避免撑爆上下文
        if len(output) > 3000:
            output = output[:3000] + f"\n... (输出已截断，共 {len(output)} 字符)"

        # 根据返回码判断命令执行状态
        status = "成功" if result.returncode == 0 else "失败"
        return f"[退出码: {result.returncode}] {status}\n{output}"

    except subprocess.TimeoutExpired:
        return f"错误: 命令 '{command}' 执行超时（{timeout} 秒），已终止"
    except FileNotFoundError:
        return f"错误: 命令不存在，或在当前环境不可用: '{command}'"
    except PermissionError:
        return f"错误: 没有权限执行命令: '{command}'"
    except Exception as e:
        return f"错误: 命令 '{command}' 执行失败: {e}"
        
