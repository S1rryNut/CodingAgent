# Git 操作工具

from ..tool import tool
from .shell_tools import run_shell_command

@tool
def git_status(directory: str = ".") -> str:
    # 获取 Git 仓库的状态
    # directory: str: Git 仓库路径，默认为当前目录
    # return: str: Git 仓库状态信息
    return run_shell_command.func(
        command="git status --short",
        cwd=directory,
        timeout=15,
    )

@tool
def git_diff(filename: str = "", directory: str = ".") -> str:
    # 获取 Git 仓库的差异信息
    # filename: str: 指定文件名，默认为空，表示获取所有文件
    # directory: str: Git 仓库路径，默认为当前目录
    # return: str: Git 仓库差异信息
    if filename:
        command = f"git diff -- {filename}"
    else:
        command = "git diff"

    return run_shell_command.func(
        command=command,
        cwd=directory,
        timeout=15,
    )

@tool
def git_commit(message: str, directory: str = ".") -> str:
    # 提交 Git 仓库的更改
    # message: str: 提交信息
    # directory: str: Git 仓库路径，默认为当前目录
    # return: str: Git 提交结果

    # 先执行 git add -A，将所有更改添加到暂存区
    add_result = run_shell_command.func(
        command="git add -A",
        cwd=directory,
        timeout=15,
    )
    if "[退出码: 0]" not in add_result:
        return f"错误: git add 失败\n{add_result}"

    # 再执行 git commit 提交更改
    commit_result = run_shell_command.func(
        command=f"git commit -m \"{message}\"",
        cwd=directory,
        timeout=15,
    )
    return commit_result