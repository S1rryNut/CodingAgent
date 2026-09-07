# Coding Agent

基于自研 ReAct Agent 框架扩展的 AI 编程助手，内置 **TDD（测试驱动开发）循环**，能自动完成"写测试 → 跑测试（RED）→ 写实现 → 再跑测试（GREEN）"的完整开发流程。

## 功能特性

- 🔧 **自研 ReAct 循环**：Thought → Action → Observation 主循环，LLM 自主决定调用哪些工具
- 🧪 **TDD 模式**：强制先写测试再写实现，红绿循环直到全部通过
- 🗺️ **Repo Map**：从代码库提取关键符号（函数/类/导入），按重要性排序生成 token 预算内的代码地图
- 🧠 **三层记忆**：
  - 短期记忆（对话历史，超预算自动压缩摘要）
  - 任务状态（目标/步骤/约束，自动维护）
  - 项目记忆（技术栈/编码规范/经验教训，持久化到 `.coding_agent/project_memory.json`）
- 🛠️ **9 个内置工具**：文件读写改、Shell 命令、代码搜索、Git 操作
- 🔄 **工具调用容错**：参数容错解析（markdown 代码块/单引号/末尾逗号/控制字符）、执行错误回填给 LLM 自行修正
- 📊 **Token 精确计数**：基于 tiktoken，超预算自动压缩旧消息为摘要

## 项目结构

```
src/coding_agent/
├── agent.py              # CodingAgent 主控（ReAct 循环）
├── tdd.py                # TDDAgent（TDD 流程指令，继承 CodingAgent）
├── main.py               # 命令行入口
├── llm.py                # LLM 客户端封装（OpenAI 兼容，tenacity 重试）
├── tool.py               # @tool 装饰器、Tool 类、ToolRegistry（自动生成 JSON Schema）
├── repo_map.py           # 代码库地图（AST 提取符号 + 重要性评分）
├── errors.py             # 自定义异常
├── memory/
│   ├── short_term.py     # 短期记忆（滑动窗口 + 自动压缩）
│   ├── task_state.py     # 任务状态
│   └── project_memory.py # 项目记忆（持久化）
├── tools/
│   ├── file_tools.py     # read_file / write_file / edit_file / list_files
│   ├── shell_tools.py    # run_shell_command
│   ├── code_search.py    # grep_code / glob_files
│   └── git_tools.py      # git_status / git_diff / git_commit
└── utils/
    ├── token_counter.py  # tiktoken 精确计数
    └── json_parser.py    # 容错 JSON 解析
```

## 安装

```bash
# 1. 创建虚拟环境
python -m venv .venv

# 2. 安装依赖
.venv\Scripts\pip install -e ".[dev]"        # Windows
# source .venv/bin/pip install -e ".[dev]"   # Linux/macOS

# 3. 配置 API Key（复制 .env.example 为 .env，填入你的 Key）
#    支持 DeepSeek 或 DashScope（阿里云百炼）
```

## 使用

```bash
# 普通模式：让 Agent 直接完成任务
.venv\Scripts\python -m coding_agent.main "写一个计算斐波那契数列的脚本"

# TDD 模式：强制先写测试再写实现
.venv\Scripts\python -m coding_agent.main --tdd "实现一个函数 is_prime(n)"

# 指定项目目录
.venv\Scripts\python -m coding_agent.main --repo D:\myproject "修复 README 中的错别字"

# 交互模式：不带任务参数启动，连续输入任务
.venv\Scripts\python -m coding_agent.main
```

## TDD 模式工作流程

```
用户需求
    │
    ▼
① 先写测试（RED）─── pytest 跑 → 测试失败（因为实现还没写）
    │
    ▼
② 分析失败原因，写最小实现
    │
    ▼
③ 再跑测试（GREEN）── 通过？→ 完成；失败？→ 回到 ②
    │
    ▼
④ 全部通过 → 总结
```

## 测试

```bash
.venv\Scripts\python test_all_tmp.py   # 全模块测试（fake LLM，不耗 API）
```

## 技术要点

- **消息序列**：严格遵守 OpenAI Function Calling 格式（assistant 带 tool_calls → tool 带 tool_call_id），tool 消息缺少 tool_call_id 会报 400
- **工具错误处理**：工具不抛异常，返回错误字符串给 LLM 自行修正
- **输出截断**：工具结果截断（3000 字符/100 字符），防止撑爆上下文
- **Windows 兼容**：所有工具均适配 Windows/PowerShell 环境

## License

MIT
