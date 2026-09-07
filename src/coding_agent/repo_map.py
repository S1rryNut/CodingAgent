# 代码库地图
# 从项目代码中提取关键符号（函数、类、方法），按重要性排序生成一份"地图"，在 token 预算内让 LLM 快速了解项目结构。

import ast
from pathlib import Path
from .utils.token_counter import count_tokens

class RepoMap:
    # 初始化 RepoMap 类
    def __init__(self, repo_path: str, token_budget: int = 3000):
        self.repo_path = Path(repo_path)
        self.token_budget = token_budget

        self.excluded_dirs = {
            ".git", "__pycache__", "node_modules",
            ".venv", "venv", "dist", "build",
            ".coding_agent", ".idea", ".vscode",
            ".pytest_cache", ".mypy_cache", ".ruff_cache",
        }
    def build_map(self) -> str:
        # 构建代码库地图

        # 1. 收集所有 Python 文件
        py_files = self._collect_python_files()

        # 2. 提取关键符号
        file_entries = []
        for file_path in py_files:
            symbols = self._extract_symbols(file_path)
            if not symbols:
                continue
            # 计算文件的重要性分数
            score = self._score_file(file_path, symbols)
            file_entries.append((file_path, symbols, score))

        # 3. 按重要性排序
        file_entries.sort(key=lambda e: e[2], reverse=True)

        # 4. 在 token 预算内组装地图
        lines = ["=== 代码库地图 ==="]
        used_tokens = 0
        shown_count = 0

            # 逐个添加文件到地图中
        for file_path, symbols, score in file_entries:
            block_lines = [str(file_path)]
            for symbol in symbols:
                block_lines.append(f"    {symbol}")
            block = "\n".join(block_lines)
            block_tokens = count_tokens(block)
            if used_tokens + block_tokens > self.token_budget and shown_count > 0:
                break
            lines.append(block)
            lines.append("")
            used_tokens += block_tokens
            shown_count += 1


        # 5. 剩余文件一行带过
        remaining_count = len(file_entries) - shown_count
        if remaining_count > 0:
            remaining_names = ", ".join(
                str(entry[0]) for entry in file_entries[shown_count:shown_count + 10]
            )
            lines.append(f"... (另有 {remaining_count} 个文件未展示: {remaining_names}...)")

        lines.append("==================")
        return "\n".join(lines)
    def _collect_python_files(self):
        # 收集所有 Python 文件，排除指定目录
        py_files = []
        for path in self.repo_path.rglob("*.py"):  # type: ignore
            if any(part in self.excluded_dirs for part in path.parts):
                continue
            py_files.append(path)
        return py_files

    def _extract_symbols(self, file_path: Path) -> list[str]:
        # 
        try:
            source = file_path.read_text(encoding="utf-8",errors="replace")
            tree = ast.parse(source)
        except (SyntaxError, IOError):
            return []

        symbols = []
        for node in ast.walk(tree):
            # 函数定义
            if isinstance(node, ast.FunctionDef):
                args = [arg.arg for arg in node.args.args]  
                symbols.append(f"Def {node.name}({', '.join(args)})")
            # 类定义
            elif isinstance(node, ast.ClassDef):
                symbols.append(f"Class: {node.name}")
            # 导入
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    symbols.append(f"Import: {alias.name}")
            # 从模块导入
            elif isinstance(node, ast.ImportFrom):
                names = [alias.name for alias in node.names]
                symbols.append(f"from {node.module} import {', '.join(names[:5])}")

        # 只保留顶层符号（不重复嵌套的）
        return symbols[:30] # 限制每个文件最多提取30个符号

    def _score_file(self, file_path: Path, symbols: list[str]) -> float:
        # 计算文件的重要性分数

        score = 0.0
        # 相对深度：越浅越重要
        rel_path = file_path.relative_to(self.repo_path)
        depth = len(rel_path.parts) - 1
        score += max(0, 10 - depth)  # 根目录 10 分，每深一层减 1
        
        # 符号数量
        score += min(len(symbols) * 0.5, 10)

        # 测试文件加分
        if "test" in file_path.stem or "tests" in rel_path.parts:
            score += 2

        # 入口文件加分
        if file_path.stem in ("main", "app", "cli", "__main__"):
            score += 3

        return score


