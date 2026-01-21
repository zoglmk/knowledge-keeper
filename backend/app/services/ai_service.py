"""
AI 服务层
支持多种 AI 模型提供商的统一接口
包括: OpenAI, Claude, Gemini, 豆包, Deepseek
"""

import httpx
import json
from typing import Optional, List, Dict, Any, AsyncGenerator
from abc import ABC, abstractmethod

from ..core.config import settings


class BaseAIClient(ABC):
    """AI 客户端基类"""
    
    @abstractmethod
    async def chat(self, messages: List[Dict], stream: bool = False) -> str:
        """发送聊天请求"""
        pass
    
    @abstractmethod
    async def chat_stream(self, messages: List[Dict]) -> AsyncGenerator[str, None]:
        """流式聊天请求"""
        pass


class OpenAICompatibleClient(BaseAIClient):
    """
    OpenAI 兼容客户端
    适用于: OpenAI, Deepseek, 豆包 等兼容 OpenAI API 的服务
    """
    
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def chat(self, messages: List[Dict], stream: bool = False) -> str:
        """发送聊天请求"""
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    async def chat_stream(self, messages: List[Dict]) -> AsyncGenerator[str, None]:
        """流式聊天请求"""
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, headers=self.headers, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            content = data["choices"][0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue


class ClaudeClient(BaseAIClient):
    """Claude API 客户端"""
    
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.anthropic.com/v1"
        self.headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
    
    async def chat(self, messages: List[Dict], stream: bool = False) -> str:
        """发送聊天请求"""
        url = f"{self.base_url}/messages"
        
        # 转换消息格式 (OpenAI 格式 -> Claude 格式)
        claude_messages = []
        system_message = None
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                claude_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        payload = {
            "model": self.model,
            "messages": claude_messages,
            "max_tokens": 2000
        }
        if system_message:
            payload["system"] = system_message
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]
    
    async def chat_stream(self, messages: List[Dict]) -> AsyncGenerator[str, None]:
        """流式聊天请求"""
        url = f"{self.base_url}/messages"
        
        claude_messages = []
        system_message = None
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                claude_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        payload = {
            "model": self.model,
            "messages": claude_messages,
            "max_tokens": 2000,
            "stream": True
        }
        if system_message:
            payload["system"] = system_message
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, headers=self.headers, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            if data.get("type") == "content_block_delta":
                                text = data.get("delta", {}).get("text", "")
                                if text:
                                    yield text
                        except json.JSONDecodeError:
                            continue


class GeminiClient(BaseAIClient):
    """Google Gemini API 客户端"""
    
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
    
    async def chat(self, messages: List[Dict], stream: bool = False) -> str:
        """发送聊天请求"""
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        
        # 转换消息格式
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            if msg["role"] == "system":
                # Gemini 没有 system role，添加到第一个 user 消息
                continue
            contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 2000
            }
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
    
    async def chat_stream(self, messages: List[Dict]) -> AsyncGenerator[str, None]:
        """流式聊天请求 (Gemini 简化版，暂不支持真正的流式)"""
        result = await self.chat(messages)
        yield result


class AIService:
    """
    AI 服务统一接口
    根据配置自动选择对应的 AI 提供商
    """
    
    def __init__(self, provider: Optional[str] = None):
        """
        初始化 AI 服务
        
        Args:
            provider: AI 提供商，可选值: openai, claude, gemini, doubao, deepseek
                     如果为 None，则使用配置文件中的默认值
        """
        self.provider = provider or settings.ai_provider
        self.client = self._create_client()
    
    def _create_client(self) -> BaseAIClient:
        """根据提供商创建对应的客户端"""
        if self.provider == "openai":
            return OpenAICompatibleClient(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                model=settings.openai_model
            )
        elif self.provider == "claude":
            return ClaudeClient(
                api_key=settings.claude_api_key,
                model=settings.claude_model
            )
        elif self.provider == "gemini":
            return GeminiClient(
                api_key=settings.gemini_api_key,
                model=settings.gemini_model
            )
        elif self.provider == "doubao":
            return OpenAICompatibleClient(
                api_key=settings.doubao_api_key,
                base_url=settings.doubao_base_url,
                model=settings.doubao_model
            )
        elif self.provider == "deepseek":
            return OpenAICompatibleClient(
                api_key=settings.deepseek_api_key,
                base_url=settings.deepseek_base_url,
                model=settings.deepseek_model
            )
        else:
            raise ValueError(f"不支持的 AI 提供商: {self.provider}")
    
    async def chat(self, messages: List[Dict], stream: bool = False) -> str:
        """
        发送聊天请求
        
        Args:
            messages: 消息列表，格式: [{"role": "user/assistant/system", "content": "..."}]
            stream: 是否使用流式响应
        
        Returns:
            AI 响应内容
        """
        return await self.client.chat(messages, stream)
    
    async def chat_stream(self, messages: List[Dict]) -> AsyncGenerator[str, None]:
        """流式聊天请求"""
        async for chunk in self.client.chat_stream(messages):
            yield chunk
    
    async def summarize(self, content: str, max_length: int = 200) -> str:
        """
        生成内容摘要
        
        Args:
            content: 原始内容
            max_length: 摘要最大长度
        
        Returns:
            摘要文本
        """
        messages = [
            {
                "role": "system",
                "content": f"你是一个专业的内容摘要助手。请将用户提供的内容总结成不超过{max_length}字的简洁摘要。摘要应该捕捉核心要点，使用清晰的中文表达。"
            },
            {
                "role": "user",
                "content": f"请为以下内容生成摘要：\n\n{content}"
            }
        ]
        return await self.chat(messages)
    
    async def generate_tags(self, content: str, existing_tags: List[str] = None, max_tags: int = 5) -> List[str]:
        """
        为内容生成标签
        
        Args:
            content: 内容文本
            existing_tags: 已有的标签列表（优先使用这些标签）
            max_tags: 最大标签数量
        
        Returns:
            标签列表
        """
        existing_prompt = ""
        if existing_tags:
            existing_prompt = f"\n\n已有标签供参考（如果合适请优先使用）: {', '.join(existing_tags)}"
        
        messages = [
            {
                "role": "system",
                "content": f"""你是一个专业的内容分类助手。请为用户提供的内容生成合适的标签。
要求：
1. 返回 1-{max_tags} 个最相关的标签
2. 每个标签 2-4 个字
3. 使用中文
4. 只返回标签，用逗号分隔，不要有其他文字{existing_prompt}"""
            },
            {
                "role": "user",
                "content": f"请为以下内容生成标签：\n\n{content[:2000]}"  # 限制长度
            }
        ]
        
        response = await self.chat(messages)
        # 解析返回的标签 - 支持多种分隔符
        import re
        # 使用中文逗号、英文逗号、顿号分割
        raw_tags = re.split(r'[,，、\n]', response)
        tags = [tag.strip() for tag in raw_tags if tag.strip() and len(tag.strip()) <= 10]
        return tags[:max_tags]
    
    async def answer_with_context(
        self, 
        question: str, 
        context: List[Dict[str, str]], 
        conversation_history: List[Dict] = None
    ) -> str:
        """
        基于上下文回答问题 (RAG)
        
        Args:
            question: 用户问题
            context: 相关上下文列表，格式: [{"title": "...", "content": "..."}]
            conversation_history: 对话历史
        
        Returns:
            AI 回答
        """
        # 构建上下文文本
        context_text = "\n\n".join([
            f"【{item['title']}】\n{item['content'][:1000]}"  # 限制每个上下文的长度
            for item in context
        ])
        
        system_prompt = f"""你是一个智能知识助手，基于用户的知识库来回答问题。

以下是从用户知识库中检索到的相关内容：

{context_text}

请根据以上内容回答用户的问题。要求：
1. 如果知识库中有相关信息，请基于这些信息回答
2. 回答要准确、有条理
3. 如果知识库中没有相关信息，请诚实告知
4. 使用中文回答"""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # 添加对话历史
        if conversation_history:
            for msg in conversation_history[-6:]:  # 只保留最近 6 条
                messages.append(msg)
        
        messages.append({"role": "user", "content": question})
        
        return await self.chat(messages)
