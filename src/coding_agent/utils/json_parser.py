# 容错JSON解析器
# LLM返回的JSON经常不规范，这个模块提供多种容错策略

import json
import re
import ast


def _fix_trailing_commas(text: str) -> str:
    # 修复 JSON 字符串末尾的逗号问题
    return re.sub(r',(\s*[}\]])', r'\1', text)


def parse_json_robust(text: str):
    # 尝试多种策略解析 JSON 字符串
    if not text or not text.strip():
        raise ValueError("空字符串，无法解析 JSON")

    text = text.strip()

    # 1：直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2：去掉 markdown 代码块
    # 匹配 ```json ... ``` 或 ``` ... ```
    code_block_pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
    match = re.search(code_block_pattern, text, re.DOTALL)
    if match:
        candidate = match.group(1).strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # 代码块里也可能有末尾逗号等问题，继续往下试
            text = candidate

    # 3：提取最外层的 {...} 或 [...]
    for pattern in [r'\{.*\}', r'\[.*\]']:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            candidate = match.group(0)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                text = candidate
                break

    # 4：修复末尾逗号 {"a": 1,} → {"a": 1}
    fixed = _fix_trailing_commas(text)
    if fixed != text:
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            text = fixed

    # 5：strict=False，允许字符串中出现未转义的控制字符
    # （换行符、制表符等）
    try:
        return json.loads(text, strict=False)
    except json.JSONDecodeError:
        pass

    # 6：ast.literal_eval 处理单引号格式
    # LLM 有时返回 Python 字典格式：{'name': 'O'Brien'}
    # ast.literal_eval 能正确处理字符串内容里的单引号，
    # 不会像 replace("'", '"') 那样破坏内容
    try:
        result = ast.literal_eval(text)
        if isinstance(result, (dict, list)):
            return result
    except (ValueError, SyntaxError):
        pass

    raise ValueError(f"无法解析 JSON: {text[:200]}")
