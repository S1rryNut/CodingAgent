# 短期记忆
# 保存对话历史，支持滑动窗口和自动压缩。超过 token 预算时，把旧消息摘要成一条 system 消息。

from ..utils.token_counter import count_messages_tokens

class ShortTermMemory:
    # 短期记忆类，保存对话历史，支持滑动窗口和自动压缩
    # token_budget: int = 2000 # token 预算
    # compression_ratio: float = 0.5 # 压缩比例，超过预算
    # messages: list[dict] = [] # 对话历史消息列表
    # _summary_cache: str | None = None # 压缩后的摘要缓存
    def __init__(self, token_budget: int = 2000, compression_ratio: float = 0.5):
        self.token_budget = token_budget # token 预算
        self.compression_ratio = compression_ratio # 压缩比例
        self.messages: list[dict] = [] # 对话历史消息列表
        self._summary_cache: str | None = None # 压缩后的摘要缓存

    # 添加消息、获取消息、获取 token 数量、压缩消息、清空消息等方法
    def add_message(
            self,
            role: str,
            content: str,
            tool_calls: list[dict] | None = None,
            tool_call_id: str | None = None
        ):
        # 添加一条消息到对话历史
        # role: str: 消息角色，user/assistant/system
        # content: str: 消息内容
        # tool_calls: list[dict] | None: 工具调用信息
        # tool_call_id: str | None: 工具调用 ID
        message = {"role": role}
        if content:
            message["content"] = content
        if tool_calls:
            message["tool_calls"] = tool_calls
        if tool_call_id:    
            message["tool_call_id"] = tool_call_id
        self.messages.append(message)

    def get_messages(self) -> list[dict]:
        # 获取对话历史消息列表，超过 token 预算时自动压缩
        # returns: list[dict]: 对话历史消息列表

        result = []
        if self._summary_cache:
            # 如果有摘要缓存，先添加摘要消息
            summary_message = {"role": "system", "content": f"[历史对话摘要]\n {self._summary_cache}"}
            result.append(summary_message)  

        # 添加原始消息
        result.extend(self.messages)
        return result

    def get_token_count(self) -> int:
        # 获取当前对话历史的 token 数量
        # returns: int: token 数量
        return count_messages_tokens(self.get_messages())

    async def compress_if_needed(self, llm_client) -> bool: 
        # 检查是否超过 token 预算，如果超过则进行压缩
        if self.get_token_count() <= self.token_budget:
            return False

        # 计算需要保留的消息数量，保留最近的消息，压缩旧消息
        keep_count = max(1, int(len(self.messages) * self.compression_ratio)) # 保留的消息数量
        messages_to_compress = self.messages[:-keep_count] # 需要压缩的消息
        remaining_messages = self.messages[-keep_count:] # 保留的消息

        if not messages_to_compress:
            return False
        # 调用 LLM 生成摘要
        summary_prompt = await self._generate_summary_prompt(llm_client, messages_to_compress)

        if self._summary_cache:
            # 如果已有摘要缓存，则将新摘要与旧摘要合并
            summary_prompt = f"[历史对话摘要]\n{self._summary_cache}\n\n[新历史对话]\n{summary_prompt}"
        else:
            summary_prompt = f"[新历史对话]\n{summary_prompt}"

        self._summary_cache = summary_prompt # 更新摘要缓存

        # 更新消息列表，移除已压缩的消息
        self.messages = remaining_messages
        return True 

    async def _generate_summary_prompt(self, llm_client, messages_to_compress: list[dict]) -> str:
        # 调用 LLM 生成摘要提示
        # messages_to_compress: list[dict]: 需要压缩的消息列表
        # returns: str: 摘要提示

        # 构建摘要请求消息
        summary_request = []
        for msg in messages_to_compress:
            role = msg["role"]
            content = msg.get("content", "")
            if role == "tool":
                summary_request.append(f"[工具结果] {content}")
            elif role == "assistant" and msg.get("tool_calls"):
                names = [tc["name"] for tc in msg["tool_calls"]]
                summary_request.append(f"[助手调用工具: {', '.join(names)}] {content or ''}")
            else:
                summary_request.append(f"[{role}] {content or ''}")

        summary_request_messages = "\n".join(summary_request)

        # 调用 LLM 生成摘要
        prompt = f"""
        请简要总结以下对话历史的关键信息，保留：
        1. 用户的原始需求
        2. 已经完成的工作
        3. 当前的状态和待解决的问题
        4. 重要的工具调用和结果

        不要超过 200 字。

        对话历史：
        {summary_request_messages}
        """

        response = await llm_client.achat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return response["content"] or ""

    def clear(self):
        # 清空对话历史和摘要缓存
        self.messages.clear()
        self._summary_cache = None

    def __len__(self) -> int:
        # 返回对话历史消息的数量
        return len(self.messages)