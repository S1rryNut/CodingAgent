#Token 计数工具
# 默认用 cl100k_base 编码（gpt-3.5-turbo/gpt-4 同款），
# 支持指定模型名自动选择对应编码。

import tiktoken

# 缓存 encoder，避免每次重复加载
_encoder_cache = {}


def _get_encoder(model: str = None):
    # 获取指定模型的编码器，如果模型不支持则降级到 cl100k_base
    cache_key = model or "default"

    # 如果缓存中已有，直接返回
    if cache_key in _encoder_cache:
        return _encoder_cache[cache_key]

    try:
        if model:
            encoder = tiktoken.encoding_for_model(model) # 获取指定模型的编码器
        else:
            encoder = tiktoken.get_encoding("cl100k_base") # 获取默认编码器
    except Exception:
        # 不支持的模型名，降级到 cl100k_base
        encoder = tiktoken.get_encoding("cl100k_base")

    _encoder_cache[cache_key] = encoder
    return encoder


def count_tokens(text: str, model: str = None) -> int:
    # 估算文本的 token 数量
    if not text:
        return 0

    encoder = _get_encoder(model) 
    return len(encoder.encode(text))


def count_messages_tokens(messages: list[dict], model: str = None) -> int:
    # 估算对话消息列表的 token 数量
    encoder = _get_encoder(model)
    total = 0

    # 每条消息的 token 计数规则：
    # - role: 计数
    # - content: 计数
    # - tool_calls: 计数（如果有）
    # - tool_call_id: 计数（如果有）
    for msg in messages:
        # role 计数
        role = msg.get("role", "")
        total += len(encoder.encode(role))

        # content 计数
        content = msg.get("content")
        if content:
            total += len(encoder.encode(content))

        # tool_calls 计数
        tool_calls = msg.get("tool_calls")
        if tool_calls:
            for tc in tool_calls:
                total += len(encoder.encode(tc.get("name", "")))
                total += len(encoder.encode(tc.get("arguments", "")))

        # tool_call_id（tool 角色的消息有这个字段）
        tool_call_id = msg.get("tool_call_id")
        if tool_call_id:
            total += len(encoder.encode(tool_call_id))

        # 每条消息的固定格式开销
        total += 4

    # 整个对话的固定开销
    total += 2

    return total
