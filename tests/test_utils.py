"""测试 utils：token_counter 和 json_parser"""

from coding_agent.utils.token_counter import count_tokens, count_messages_tokens
from coding_agent.utils.json_parser import parse_json_robust


def test_token_counter():
    print("=== 测试 token_counter ===")

    # 英文
    print(f"'hello world' ({len('hello world')} 字符): {count_tokens('hello world')} tokens")

    # 中文
    print(f"'你好世界' ({len('你好世界')} 字符): {count_tokens('你好世界')} tokens")

    # 混合
    mixed = "Hello 你好 World 世界"
    print(f"'{mixed}' ({len(mixed)} 字符): {count_tokens(mixed)} tokens")

    # 空字符串
    print(f"空字符串: {count_tokens('')} tokens")

    # 对话历史
    messages = [
        {"role": "system", "content": "你是一个助手"},
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好！有什么可以帮你的？"},
    ]
    print(f"3 条消息的对话历史: {count_messages_tokens(messages)} tokens")
    print()


def test_json_parser():
    print("=== 测试 json_parser ===")

    # 正常 JSON
    result = parse_json_robust('{"name": "test", "value": 123}')
    print(f"正常 JSON: {result}")

    # 带 markdown 代码块
    result = parse_json_robust('```json\n{"name": "test"}\n```')
    print(f"markdown 代码块: {result}")

    # 前后有多余文字
    result = parse_json_robust('好的，这是结果：\n{"expression": "1 + 2"}\n希望对你有帮助')
    print(f"前后有文字: {result}")

    # 单引号
    result = parse_json_robust("{'name': 'test', 'value': 456}")
    print(f"单引号: {result}")

    # 数组
    result = parse_json_robust('[1, 2, 3]')
    print(f"数组: {result}")

    # 解析失败
    try:
        parse_json_robust("这不是 JSON")
    except ValueError as e:
        print(f"非法 JSON 正确报错: {e}")

    print()
    print("✅ 所有测试通过")


if __name__ == "__main__":
    test_token_counter()
    test_json_parser()
