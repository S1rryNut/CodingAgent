# 项目记忆模块，用于存储和管理项目相关的知识和经验，包括技术栈、编码规范、经验教训、常见问题等。

import json
from pathlib import Path

class ProjectMemory:
    # 项目记忆类，用于管理和存储项目相关的知识和经验
    def __init__(self, workspace_dir: str):
        self.workspace_dir = Path(workspace_dir)
        self.memory_file = self.workspace_dir / "project_memory.json"
        self.memory_dir = self.workspace_dir / ".coding_agent"

        # 默认结构 
        self.data: dict = {
            "tech_stack": [],      # 技术栈
            "conventions": [],     # 编码规范
            "lessons": [],         # 经验教训
            "common_issues": [],   # 常见问题
            "custom": {},          # 自定义
        }
        self._load()  # 尝试加载已有的项目记忆数据

    def _load(self):
        # 加载项目记忆数据，如果文件存在则读取，否则使用默认结构
        if self.memory_file.exists():
            try:
                loaded_data = json.loads(self.memory_file.read_text(encoding="utf-8"))
                self.data.update(loaded_data)
            except (json.JSONDecodeError, IOError):
                pass  # 如果文件损坏或无法读取，保持默认结构

    def _save(self):
        # 保存项目记忆数据到文件，确保目录存在
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.memory_file.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


        # =====技术栈=====
    def add_tech_stack(self, tech: str):
        # 添加技术栈
        if tech not in self.data["tech_stack"]:
            self.data["tech_stack"].append(tech)
            self._save()

        # =====编码规范=====
    def add_convention(self, convention: str):
        # 添加编码规范
        if convention not in self.data["conventions"]:
            self.data["conventions"].append(convention)
            self._save()

        # =====经验教训=====
    def add_lesson(self, lesson: str):
        # 添加经验教训
        if lesson not in self.data["lessons"]:
            self.data["lessons"].append(lesson)
            self._save()


        # =====常见问题=====
    def add_common_issue(self, issue: str, solution: str):
        # 添加常见问题及其解决方案
        for item in self.data["common_issues"]:
            if item["issue"] == issue:
                return
        self.data["common_issues"].append({
            "issue": issue,
            "solution": solution,
        })
        self._save()


        # =====自定义数据=====
    def set_custom(self, key: str, value):
        # 设置自定义记忆
        self.data["custom"][key] = value
        self._save()

    def get_custom(self, key: str, default=None):
        # 获取自定义记忆
        return self.data["custom"].get(key, default)

        # ===== Prompt 生成 =====
    def to_prompt(self) -> str:
        # 将项目记忆转换为提示字符串，用于 LLM 输入
        lines = []

        if self.data["tech_stack"]:
            lines.append("技术栈：")
            for tech in self.data["tech_stack"]:
                lines.append(f"  - {tech}")

        if self.data["conventions"]:
            lines.append("编码规范：")
            for convention in self.data["conventions"]:
                lines.append(f"  - {convention}")

        if self.data["lessons"]:
            lines.append("经验教训：")
            for lesson in self.data["lessons"][-5:]:  # 只显示最近的5条经验教训
                lines.append(f"  - {lesson}")

        if self.data["common_issues"]:
            lines.append("常见问题：")
            for issue in self.data["common_issues"][-3:]:
                lines.append(f"  - 问题: {issue['issue']}, 解决方案: {issue['solution']}")

        return "=== 项目记忆 ===\n" + "\n".join(lines) + "\n=================="

        # ===== 工具方法 =====

    def has_content(self) -> bool:
        # 检查项目记忆是否有内容
        return any([
            self.data["tech_stack"],
            self.data["conventions"],
            self.data["lessons"],
            self.data["common_issues"],
            self.data["custom"],
        ])

    def clear(self):
        # 清空项目记忆
        self.data = {
            "tech_stack": [],
            "conventions": [],
            "lessons": [],
            "common_issues": [],
            "custom": {},
        }
        self._save()