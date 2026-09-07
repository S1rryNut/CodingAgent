# Coding Agent 技术设计文档

## 1. 项目概述

基于自研 ReAct Agent 框架扩展的 AI 编程助手，能够理解代码库、自动编写代码、运行测试、修复错误，实现测试驱动开发（TDD）的完整闭环。

### 1.1 核心能力

- **代码库理解**：通过 Repo Map 快速了解项目结构、函数签名、调用关系
- **文件操作**：读取、创建、精细编辑（search/replace）、删除文件
- **命令执行**：运行测试、安装依赖、执行构建，带超时和输出截断
- **代码搜索**：按符号名、正则表达式在代码库中搜索
- **Git 集成**：查看 diff、创建分支、提交代码
- **TDD 循环**：先写测试 → 跑测试看失败 → 写实现 → 再跑测试 → 直到全绿
- **多轮对话**：支持上下文连续对话，自动维护任务状态

### 1.2 设计原则

- **不依赖 LangChain**：基于自研 ReAct 框架，完全可控
- **工具优先**：所有操作通过工具完成，Agent 只负责决策
- **安全第一**：文件操作前备份，命令执行有超时，危险操作需确认
- **可观测**：每一步工具调用都有详细日志，便于调试
- **渐进增强**：先跑通核心循环，再加复杂特性

---

## 2. 技术栈

| 层级 | 技术 | 说明 |
|---|---|---|
| 语言 | Python 3.11+ | 与 Agent 框架一致 |
| LLM | DashScope qwen-plus / DeepSeek | OpenAI 兼容 API |
| 异步 | asyncio + httpx | 异步 LLM 调用和工具执行 |
| 重试 | tenacity | API 调用失败自动重试 |
| 代码解析 | tree-sitter（可选，第一版用正则） | 提取函数/类签名 |
| 图算法 | networkx（可选） | Repo Map 的 PageRank 排序 |
| 测试 | pytest | 项目自身测试 |
| 前端 | React + Vite + AntD（后续） | 聊天界面 + 文件树 + 终端输出 |
| 包管理 | uv | 依赖管理和虚拟环境 |

---

## 3. 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                      Coding Agent                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐    ┌──────────────┐                  │
│  │  ReAct Loop  │◄──►│  LLM Client  │                  │
│  │  (agent.py)  │    │   (llm.py)   │                  │
│  └──────┬───────┘    └──────────────┘                  │
│         │                                               │
│  ┌──────▼───────┐    ┌──────────────┐                  │
│  │  Tool Registry│◄──►│ Coding Tools │                  │
│  │  (tool.py)   │    │              │                  │
│  └──────────────┘    │ ┌──────────┐ │                  │
│                      │ │ File     │ │                  │
│  ┌──────────────┐    │ │ Editor   │ │                  │
│  │   Memory     │    │ ├──────────┤ │                  │
│  │  (简化版)    │    │ │ Shell    │ │                  │
│  │              │    │ │ Executor │ │                  │
│  │ 短期记忆      │    │ ├──────────┤ │                  │
│  │ 任务状态      │    │ │ Code     │ │                  │
│  │ 项目记忆      │    │ │ Search   │ │                  │
│  └──────────────┘    │ ├──────────┤ │                  │
│                      │ │ Git      │ │                  │
│  ┌──────────────┐    │ │ Tools    │ │                  │
│  │  Repo Map    │    │ └──────────┘ │                  │
│  │ (代码库地图)  │    └──────────────┘                  │
│  │              │                                      │
│  │ AST 解析      │    ┌──────────────┐                  │
│  │ 引用图        │◄──►│  TDD Loop    │                  │
│  │ PageRank 排序 │    │ (核心创新)   │                  │
│  │ Token 预算    │    │              │                  │
│  └──────────────┘    │ 写测试        │                  │
│                      │ 跑测试        │                  │
│                      │ 解析失败      │                  │
│                      │ 写实现        │                  │
│                      │ 循环直到通过   │                  │
│                      └──────────────┘                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 4. 核心模块设计

### 4.1 LLM 客户端（llm.py）

**复用 Agent 项目的设计**，做少量调整：

- 基于 `AsyncOpenAI`，支持 OpenAI 兼容 API（DashScope、DeepSeek）
- tenacity 重试，只重试 429 和 5xx
- 支持 tool_calls，返回结构化结果
- 支持流式输出（后续前端需要）

```python
class LLMClient:
    def __init__(self, model, api_key, base_url=None, timeout=60.0, max_retries=3):
        ...

    async def achat(self, messages, tools=None, temperature=0.7, max_tokens=None):
        """返回 {content, tool_calls, finish_reason, usage}"""
        ...
```

### 4.2 工具系统（tool.py）

**复用 Agent 项目的 @tool 装饰器**，自动从函数签名生成 JSON Schema。

```python
def tool(func):
    """装饰器：将函数转为 Tool 对象，自动生成 JSON Schema"""
    ...

class Tool:
    name: str
    description: str
    schema: dict          # JSON Schema
    func: Callable        # 同步或异步函数

    async def invoke(self, arguments: dict) -> str:
        """执行工具，返回字符串结果"""
        ...

class ToolRegistry:
    def register(self, tool: Tool): ...
    def get(self, name: str) -> Tool: ...
    def get_schemas(self) -> list[dict]: ...
    async def execute(self, name: str, arguments: dict) -> str: ...
```

### 4.3 记忆系统（简化版）

基于之前的分析，Coding Agent 不需要完整的三层记忆，简化为：

#### 4.3.1 短期记忆（short_term.py）

- 滑动窗口保存最近 N 轮对话
- 超出窗口时，对旧消息做摘要
- 自动管理 token 预算

```python
class ShortTermMemory:
    def __init__(self, max_tokens=4000, summary_model=None):
        self.messages = []
        self.max_tokens = max_tokens

    def add(self, role: str, content: str):
        """添加消息，超出预算时自动压缩"""
        ...

    def get_messages(self) -> list[dict]:
        """返回当前上下文中的消息"""
        ...

    def _compress(self):
        """将旧消息压缩为一条摘要"""
        ...
```

#### 4.3.2 任务状态（task_state.py）

**框架自动维护，不需要 Agent 主动调用。**

- 记录当前任务描述
- 记录已执行的步骤（工具调用历史）
- 记录最近的工具结果
- 每轮自动更新，作为 system prompt 的一部分

```python
class TaskState:
    def __init__(self):
        self.goal = ""              # 当前任务目标
        self.steps = []             # 已执行的步骤
        self.last_tool_result = ""  # 最近的工具结果
        self.constraints = []       # 约束条件

    def set_goal(self, goal: str): ...
    def add_step(self, step: str): ...
    def set_last_result(self, result: str): ...
    def to_prompt(self) -> str:
        """生成任务状态的 prompt 片段"""
        ...

    def reset(self): ...
```

#### 4.3.3 项目记忆（project_memory.py）

**替代长期记忆，存在项目目录下。**

- 记录项目的技术栈、代码规范、常见坑
- 由 Repo Map 自动提取，或 Agent 主动写入
- 文件路径：`{project_root}/.coding_agent/memory.json`

```python
class ProjectMemory:
    def __init__(self, project_root: str):
        self.path = os.path.join(project_root, ".coding_agent", "memory.json")
        self.data = self._load()

    def get(self, key: str, default=None): ...
    def set(self, key: str, value): ...
    def save(self): ...
    def to_prompt(self) -> str: ...
```

### 4.4 ReAct Agent 循环（agent.py）

核心循环，复用 Agent 项目的设计，集成简化版记忆和任务状态。

```python
class CodingAgent:
    def __init__(
        self,
        llm: LLMClient,
        registry: ToolRegistry,
        project_root: str,
        memory: ShortTermMemory = None,
        task_state: TaskState = None,
        project_memory: ProjectMemory = None,
        repo_map: RepoMap = None,
        max_iterations: int = 30,
        verbose: bool = True,
    ):
        ...

    async def arun(self, task: str) -> str:
        """执行任务，返回最终结果"""
        # 1. 设置任务目标
        # 2. 构建 system prompt（角色 + 项目记忆 + Repo Map + 任务状态）
        # 3. ReAct 循环：
        #    - 调用 LLM
        #    - 如果有 tool_calls，执行工具，记录结果
        #    - 如果没有 tool_calls，返回最终回答
        # 4. 达到最大迭代次数则报错
        ...

    def _build_system_prompt(self) -> str:
        """构建 system prompt，包含：
        - 角色定义
        - 项目记忆
        - Repo Map（动态生成）
        - 任务状态
        - 工具使用规范
        """
        ...
```

### 4.5 Coding 专用工具

这是 Coding Agent 与通用 Agent 最大的区别。所有工具都限制在 `project_root` 目录内，防止越权操作。

#### 4.5.1 文件工具（file_tools.py）

| 工具名 | 功能 | 参数 |
|---|---|---|
| `read_file` | 读取文件内容 | filename, start_line, end_line |
| `write_file` | 创建/覆盖文件 | filename, content |
| `edit_file` | 精细编辑（search/replace） | filename, search_text, replace_text |
| `delete_file` | 删除文件（需确认） | filename |
| `list_files` | 列出目录文件 | path, pattern |
| `search_files` | 按内容搜索文件 | pattern, path |

**edit_file 是最核心的工具**，实现 search/replace 模式：
- 在文件中搜索 `search_text`
- 替换为 `replace_text`
- 如果有多处匹配，报错要求更精确
- 编辑前自动备份到 `.coding_agent/backups/`

```python
@tool
async def edit_file(filename: str, search_text: str, replace_text: str) -> str:
    """精细编辑文件：搜索指定文本并替换。
    search_text 必须唯一匹配，否则报错。
    编辑前自动备份。
    """
    ...
```

#### 4.5.2 Shell 工具（shell_tools.py）

| 工具名 | 功能 | 参数 |
|---|---|---|
| `run_command` | 执行 shell 命令 | command, cwd, timeout |
| `run_python` | 执行 Python 脚本 | code, cwd |
| `run_tests` | 运行测试（封装 pytest） | test_path, cwd |

**安全机制：**
- 默认超时 60 秒
- 输出截断到 4000 字符
- 禁止危险命令（rm -rf /、mkfs 等）
- 工作目录限制在 project_root 内

```python
@tool
async def run_command(command: str, cwd: str = None, timeout: int = 60) -> str:
    """执行 shell 命令，返回 stdout + stderr + 退出码。
    超时自动终止，输出自动截断。
    """
    ...
```

#### 4.5.3 代码搜索工具（code_search.py）

| 工具名 | 功能 | 参数 |
|---|---|---|
| `find_symbol` | 查找函数/类定义 | symbol_name, path |
| `grep_search` | 正则搜索代码内容 | pattern, path, file_type |
| `find_files` | 按文件名搜索 | pattern, path |

第一版用正则实现，后续可升级为 tree-sitter。

#### 4.5.4 Git 工具（git_tools.py）

| 工具名 | 功能 | 参数 |
|---|---|---|
| `git_status` | 查看工作区状态 | — |
| `git_diff` | 查看变更 diff | filename（可选） |
| `git_add` | 暂存文件 | filename |
| `git_commit` | 提交 | message |
| `git_branch` | 创建/切换分支 | name |

### 4.6 Repo Map（repo_map.py）

**Coding Agent 的核心差异化能力。**

参考 Aider 的设计，第一版用简化实现：

#### 4.6.1 工作流程

```
源码文件 → 正则提取符号 → 构建引用图 → 简单排序 → Token预算拟合 → 输出
```

#### 4.6.2 符号提取（第一版用正则）

- Python：匹配 `def`、`class`、`async def`
- JavaScript/TypeScript：匹配 `function`、`class`、`export function`
- 提取函数名、参数列表、行号

#### 4.6.3 排序策略（第一版简化版）

不用 PageRank，用简单的加权排序：
- 文件在对话中被提到：权重 ×10
- 文件被其他文件引用次数多：权重 ×(1 + 引用次数)
- 当前正在编辑的文件：权重 ×5

#### 4.6.4 Token 预算

- 默认预算：1024 tokens
- 按排序结果依次加入，直到预算用完
- 只输出符号签名，不输出函数体

#### 4.6.5 输出格式

```
src/agent.py:
  class CodingAgent:
    def __init__(self, llm, registry, project_root, ...)
    async def arun(self, task: str) -> str
    def _build_system_prompt(self) -> str

src/tools/file_tools.py:
  async def read_file(filename, start_line=None, end_line=None)
  async def write_file(filename, content)
  async def edit_file(filename, search_text, replace_text)
```

```python
class RepoMap:
    def __init__(self, project_root: str, max_tokens: int = 1024):
        self.project_root = project_root
        self.max_tokens = max_tokens
        self._cache = {}  # 文件 mtime → 符号列表

    def generate(self, context_files: list[str] = None, mentioned_files: list[str] = None) -> str:
        """生成 Repo Map
        context_files: 当前在对话中的文件，加权
        mentioned_files: 被提到的文件，加权
        """
        # 1. 扫描所有源文件，提取符号
        # 2. 构建引用关系
        # 3. 排序
        # 4. 按 token 预算截断
        # 5. 格式化输出
        ...

    def _extract_symbols(self, filepath: str) -> list[dict]:
        """从文件中提取函数/类签名"""
        ...

    def _rank_files(self, files: list[dict], context_files: list[str]) -> list[dict]:
        """对文件按相关性排序"""
        ...
```

### 4.7 TDD 循环（tdd.py）—— 核心创新点

**测试驱动开发的自动化闭环。**

```
用户给需求
    │
    ▼
┌─────────────────┐
│ 1. 理解需求      │  Agent 读代码、问澄清问题
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. 写测试        │  Agent 根据需求编写测试用例
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. 跑测试        │  run_tests 工具执行
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
  通过       失败
    │         │
    │         ▼
    │  ┌─────────────────┐
    │  │ 4. 解析失败      │  提取错误信息和失败位置
    │  └────────┬────────┘
    │           │
    │           ▼
    │  ┌─────────────────┐
    │  │ 5. 写实现        │  Agent 编写实现代码
    │  └────────┬────────┘
    │           │
    │           ▼
    │  ┌─────────────────┐
    │  │ 6. 跑测试        │  再次执行
    │  └────────┬────────┘
    │           │
    │           └──────► 回到 3，循环直到通过或达到最大轮次
    │
    ▼
┌─────────────────┐
│ 7. 完成          │  所有测试通过，返回结果
└─────────────────┘
```

```python
class TDDLoop:
    def __init__(self, agent: CodingAgent, max_rounds: int = 10):
        self.agent = agent
        self.max_rounds = max_rounds

    async def run(self, requirement: str, test_file: str = None) -> dict:
        """执行 TDD 循环
        返回 {success: bool, test_results: str, iterations: int, final_code: str}
        """
        # 1. 写测试
        # 2. 跑测试（预期失败）
        # 3. 循环：写实现 → 跑测试 → 检查结果
        # 4. 返回结果
        ...

    async def _write_tests(self, requirement: str) -> str: ...
    async def _run_tests(self, test_path: str) -> dict: ...
    def _parse_failure(self, test_output: str) -> dict:
        """解析测试失败信息，提取错误位置和原因"""
        ...
    async def _write_implementation(self, failure_info: dict) -> str: ...
```

---

## 5. 前端设计（第二阶段）

### 5.1 界面布局

```
┌─────────────────────────────────────────────────────────┐
│  Header: 项目名称 | 分支 | 状态指示器                     │
├──────────┬──────────────────────────┬───────────────────┤
│          │                          │                   │
│ 文件树   │   聊天对话区              │  代码预览/终端     │
│          │                          │                   │
│ - src/   │  ┌──────────────────┐    │  ┌─────────────┐  │
│   - agent│  │  用户: 写个计算器 │    │  │ 文件内容     │  │
│   - tools│  │                  │    │  │             │  │
│          │  │  AI: 好的，我先  │    │  │  diff 高亮   │  │
│          │  │  写测试...       │    │  │             │  │
│          │  │                  │    │  └─────────────┘  │
│          │  │  [工具调用]      │    │  ┌─────────────┐  │
│          │  │  write_file()   │    │  │ 终端输出     │  │
│          │  │  edit_file()    │    │  │ 测试结果     │  │
│          │  │  run_tests()    │    │  │             │  │
│          │  └──────────────────┘    │  └─────────────┘  │
│          │                          │                   │
│          │  [输入框] 发送按钮        │                   │
├──────────┴──────────────────────────┴───────────────────┤
│  状态栏: 当前步骤 | 迭代次数 | Token 用量                  │
└─────────────────────────────────────────────────────────┘
```

### 5.2 核心功能

- 聊天界面：流式输出、工具调用可视化（展开/收起）
- 文件树：显示项目文件，点击查看内容
- 代码预览：显示 Agent 编辑的文件，diff 高亮
- 终端输出：显示命令执行结果，支持滚动
- 任务状态：显示当前 TDD 循环进度（写测试/跑测试/写实现）
- 历史记录：保存之前的任务和对话

---

## 6. 开发计划

### 阶段一：核心循环（第 1-2 周）

- [ ] 搭环境（uv init、安装依赖）
- [ ] 移植 LLM 客户端和工具系统
- [ ] 实现简化版记忆（短期 + 任务状态）
- [ ] 实现 ReAct Agent 循环
- [ ] 实现基础文件工具（read/write/list）
- [ ] 实现 Shell 工具（run_command）
- [ ] 端到端测试：让 Agent 创建一个简单的 Python 文件并运行

### 阶段二：Coding 能力（第 2-3 周）

- [ ] 实现 edit_file（search/replace + 自动备份）
- [ ] 实现代码搜索工具（grep/find_symbol）
- [ ] 实现 Git 工具
- [ ] 实现 Repo Map（简化版）
- [ ] 集成 Repo Map 到 system prompt
- [ ] 端到端测试：让 Agent 阅读现有代码并做小修改

### 阶段三：TDD 循环（第 3-4 周）

- [ ] 实现 TDDLoop 类
- [ ] 实现测试失败解析
- [ ] 实现项目记忆
- [ ] 端到端测试：给一个需求，让 Agent 自动完成 TDD 循环
- [ ] 多轮测试：不同类型的需求（算法/工具类/Web 接口）

### 阶段四：前端（第 4-5 周）

- [ ] 搭建 React + Vite + AntD 项目
- [ ] 实现聊天界面（流式输出 + 工具调用可视化）
- [ ] 实现文件树和代码预览
- [ ] 实现终端输出面板
- [ ] 实现 TDD 进度指示器
- [ ] 前后端联调

### 阶段五：打磨和文档（第 5-6 周）

- [ ] 完善错误处理和边界情况
- [ ] 加详细日志和 trace
- [ ] 写 README
- [ ] 写使用示例和演示
- [ ] 推 GitHub

---

## 7. 目录结构

```
CodingAgent/
├── src/
│   └── coding_agent/
│       ├── __init__.py
│       ├── llm.py                  # LLM 客户端
│       ├── tool.py                 # 工具系统（@tool 装饰器 + Registry）
│       ├── agent.py                # ReAct Agent 循环
│       ├── errors.py               # 自定义异常
│       ├── memory/
│       │   ├── __init__.py
│       │   ├── short_term.py       # 短期记忆
│       │   ├── task_state.py       # 任务状态（自动维护）
│       │   └── project_memory.py   # 项目记忆
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── file_tools.py       # 文件操作工具
│       │   ├── shell_tools.py      # 命令执行工具
│       │   ├── code_search.py      # 代码搜索工具
│       │   └── git_tools.py        # Git 工具
│       ├── repo_map.py             # 代码库地图
│       ├── tdd.py                  # TDD 循环（核心创新）
│       └── utils/
│           ├── __init__.py
│           ├── token_counter.py    # Token 计数
│           └── json_parser.py      # 容错 JSON 解析
├── tests/
│   ├── __init__.py
│   ├── test_llm.py
│   ├── test_tool.py
│   ├── test_agent.py
│   ├── test_file_tools.py
│   ├── test_shell_tools.py
│   ├── test_repo_map.py
│   └── test_tdd.py
├── examples/
│   └── simple_demo.py              # 简单演示
├── frontend/                       # 第二阶段
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── pyproject.toml
├── .env.example
├── .gitignore
└── README.md
```

---

## 8. 与已有项目的关系

| 项目 | 关系 |
|---|---|
| co11ap5e_agent | 基础框架，Coding Agent 复用其 LLM 客户端、工具系统、ReAct 循环的设计 |
| co11ap5e_multi_agent | 多 Agent 经验，后续可扩展为"架构师+程序员+测试"协作编码 |
| EKP 企业知识库 | 前端经验复用，RAG 技术可用于代码库语义检索 |

四个项目形成完整体系：
```
底层框架（Agent）→ 系统协作（MultiAgent）→ 知识应用（EKP）→ 垂直落地（CodingAgent）
```

---

## 9. 风险与应对

| 风险 | 影响 | 应对 |
|---|---|---|
| LLM 不按格式调用工具 | 循环卡住 | 加容错解析，失败时重试并提示格式 |
| edit_file 匹配不唯一 | 编辑错误 | 要求唯一匹配，否则报错让 Agent 缩小范围 |
| 命令执行超时/挂起 | 阻塞 | 强制超时 + 进程终止 |
| Repo Map 不准确 | 上下文缺失 | 第一版用简化实现，验证效果后再优化 |
| TDD 循环死循环 | 浪费 token | 最大轮次限制 + 失败时人工介入 |
| 文件操作越权 | 安全风险 | 所有路径限制在 project_root 内 |
| API 额度耗尽 | 无法测试 | 支持多模型切换（DeepSeek ↔ DashScope） |

---

## 10. 成功标准

- [ ] 能自动创建一个 Python 项目并写一个简单函数
- [ ] 能阅读现有代码库，找到目标函数并修改
- [ ] 能执行 TDD 循环：给需求 → 写测试 → 写实现 → 测试通过
- [ ] 能处理测试失败，自动定位错误并修复
- [ ] 前端能展示完整的对话、工具调用、代码变更、测试结果
