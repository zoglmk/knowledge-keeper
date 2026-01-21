"""
收藏和标签相关的数据模型
"""

from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, Enum, Table
from sqlalchemy.orm import relationship
from uuid import uuid4

from ..core.database import Base


class BookmarkType(str, PyEnum):
    """收藏类型枚举"""
    URL = "url"       # 网页链接
    NOTE = "note"     # 手写笔记
    FILE = "file"     # 上传文件


# 收藏和标签的多对多关联表
BookmarkTag = Table(
    'bookmark_tags',
    Base.metadata,
    Column('bookmark_id', String(36), ForeignKey('bookmarks.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', String(36), ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True),
)


class Bookmark(Base):
    """收藏模型"""
    __tablename__ = 'bookmarks'
    
    # 主键
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # 基本信息
    title = Column(String(500), nullable=False, index=True)
    url = Column(String(2000), nullable=True)  # 原始链接（可选）
    content = Column(Text, nullable=True)       # 原始内容
    summary = Column(Text, nullable=True)       # AI 生成的摘要
    
    # 类型
    type = Column(Enum(BookmarkType), default=BookmarkType.URL, nullable=False)
    
    # 文件相关（如果是文件类型）
    file_path = Column(String(1000), nullable=True)
    file_type = Column(String(50), nullable=True)
    
    # 向量化状态
    is_embedded = Column(Boolean, default=False)
    
    # 是否已收藏（软删除标记）
    is_active = Column(Boolean, default=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关联
    tags = relationship('Tag', secondary=BookmarkTag, back_populates='bookmarks', lazy='selectin')
    
    def __repr__(self):
        return f"<Bookmark(id={self.id}, title={self.title[:30]}...)>"


class Tag(Base):
    """标签模型"""
    __tablename__ = 'tags'
    
    # 主键
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # 基本信息
    name = Column(String(100), nullable=False, unique=True, index=True)
    color = Column(String(7), default='#6366f1')  # 颜色代码
    
    # 是否为 AI 自动生成
    is_auto = Column(Boolean, default=False)
    
    # 使用次数（用于排序和推荐）
    usage_count = Column(String(10), default='0')
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 关联
    bookmarks = relationship('Bookmark', secondary=BookmarkTag, back_populates='tags', lazy='selectin')
    
    def __repr__(self):
        return f"<Tag(id={self.id}, name={self.name})>"
