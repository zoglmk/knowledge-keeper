"""
对话和消息相关的 Pydantic 模型
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class MessageRole(str, Enum):
    """消息角色"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# ==================== 来源引用 ====================

class SourceReference(BaseModel):
    """来源引用"""
    bookmark_id: str
    title: str
    url: Optional[str] = None
    relevance: float = Field(..., ge=0, le=1, description="相关度分数")
    snippet: Optional[str] = None  # 相关内容片段


# ==================== 消息模型 ====================

class MessageBase(BaseModel):
    """消息基础模型"""
    content: str = Field(..., min_length=1, description="消息内容")


class MessageCreate(MessageBase):
    """创建消息请求"""
    role: MessageRole = MessageRole.USER


class MessageResponse(BaseModel):
    """消息响应"""
    id: str
    role: MessageRole
    content: str
    sources: Optional[List[SourceReference]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== 对话模型 ====================

class ConversationBase(BaseModel):
    """对话基础模型"""
    title: str = Field(default="新对话", max_length=200)


class ConversationCreate(ConversationBase):
    """创建对话请求"""
    pass


class ConversationResponse(BaseModel):
    """对话响应"""
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []
    message_count: int = 0
    
    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """对话列表响应"""
    items: List[ConversationResponse]
    total: int


# ==================== 聊天请求/响应 ====================

class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(..., min_length=1, description="用户消息")
    conversation_id: Optional[str] = Field(None, description="对话 ID，为空则创建新对话")
    use_knowledge_base: bool = Field(default=True, description="是否使用知识库")


class ChatResponse(BaseModel):
    """聊天响应"""
    conversation_id: str
    message: MessageResponse
    sources: List[SourceReference] = []
