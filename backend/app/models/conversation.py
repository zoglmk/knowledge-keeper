"""
对话和消息相关的数据模型
"""

from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from uuid import uuid4

from ..core.database import Base


class MessageRole(str, PyEnum):
    """消息角色枚举"""
    USER = "user"           # 用户消息
    ASSISTANT = "assistant" # AI 助手消息
    SYSTEM = "system"       # 系统消息


class Conversation(Base):
    """对话模型"""
    __tablename__ = 'conversations'
    
    # 主键
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # 基本信息
    title = Column(String(200), nullable=False, default="新对话")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关联消息
    messages = relationship('Message', back_populates='conversation', 
                           lazy='selectin', order_by='Message.created_at',
                           cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, title={self.title[:30]}...)>"


class Message(Base):
    """消息模型"""
    __tablename__ = 'messages'
    
    # 主键
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # 关联对话
    conversation_id = Column(String(36), ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False)
    
    # 消息内容
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    
    # 引用来源（JSON 格式存储）
    # 格式: [{"bookmark_id": "xxx", "title": "xxx", "relevance": 0.95}, ...]
    sources = Column(JSON, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 关联
    conversation = relationship('Conversation', back_populates='messages')
    
    def __repr__(self):
        return f"<Message(id={self.id}, role={self.role}, content={self.content[:30]}...)>"
