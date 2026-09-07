# LLM 客户端封装

from openai import AsyncOpenAI
from openai import RateLimitError, APIStatusError
from tenacity import(
    retry, 
    stop_after_attempt, 
    wait_exponential, 
    retry_if_exception_type
)

class LLMClient:
    def __init__(
        self, 
        model: str,
        api_key: str,
        base_url: str | None = None,
        timeout: float = 60.0, # 请求超时时间，单位为秒
        max_retries: int = 3,
    ):
        self.model = model
        self.max_retries = max_retries
        self._client = AsyncOpenAI( # 初始化 OpenAI 客户端
            api_key=api_key, 
            base_url=base_url, 
            timeout=timeout
        )
    @retry(
        stop=stop_after_attempt(3), # 最大重试次数
        wait=wait_exponential(multiplier=1, min=2, max=10), # 等待时间
        retry=retry_if_exception_type((RateLimitError, APIStatusError)), # 重试条件
        reraise=True # 如果重试失败，抛出异常
    )

    async def _call_with_retry(self, **kwargs):
        # 调用 OpenAI API，带有重试机制
        return await self._client.chat.completions.create(**kwargs)

    async def achat(
            self, 
            messages: list[dict], 
            tools: list[dict] | None = None, 
            temperature: float = 0.7, 
            max_tokens:int | None = None
        ) -> dict:
        # 调用 OpenAI API，获取 LLM 响应
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools is not None: # 如果提供了工具列表，将其添加到请求参数中
            kwargs["tools"] = tools
        if max_tokens is not None: # 如果提供了最大 token 数，将其添加到请求参数中
            kwargs["max_tokens"] = max_tokens

        # 调用带有重试机制的 API 请求
        response = await self._call_with_retry(**kwargs)

        # 解析响应，获取第一个选择的消息
        choice = response.choices[0]
        # 获取消息内容
        message = choice.message

        # 构建结果字典，包含消息内容、工具调用信息、完成原因和使用情况
        result = {
            "content": message.content,
            "tool_calls": message.tool_calls if hasattr(message, "tool_calls") else None,
            "finish_reason": choice.finish_reason,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
        }

        # 如果消息中包含工具调用信息，将其添加到结果字典中
        if message.tool_calls is not None:
            result["tool_calls"] = [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments,
                    },
                }
                for tool_call in message.tool_calls
            ]
        return result
        
        