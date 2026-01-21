"""
收藏和标签相关的 Pydantic 模型
用于请求/响应数据验证
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum


class BookmarkType(str, Enum):
    """收藏类型"""
    URL = "url"
    NOTE = "note"
    FILE = "file"


# ==================== 标签模型 ====================

class TagBase(BaseModel):
    """标签基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="标签名称")
    color: str = Field(default="#6366f1", pattern=r"^#[0-9A-Fa-f]{6}$", description="颜色代码")


class TagCreate(TagBase):
    """创建标签请求"""
    pass


class TagResponse(TagBase):
    """标签响应"""
    id: str
    is_auto: bool = False
    usage_count: str = "0"
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== 收藏模型 ====================

class BookmarkBase(BaseModel):
    """收藏基础模型"""
    title: str = Field(..., min_length=1, max_length=500, description="标题")
    url: Optional[str] = Field(None, max_length=2000, description="原始链接")
    content: Optional[str] = Field(None, description="内容")


class BookmarkCreate(BaseModel):
    """创建收藏请求"""
    title: Optional[str] = Field(None, max_length=500, description="标题（可选，会自动提取）")
    url: Optional[str] = Field(None, max_length=2000, description="网页链接")
    content: Optional[str] = Field(None, description="手动输入的内容")
    type: BookmarkType = Field(default=BookmarkType.URL, description="收藏类型")
    tags: List[str] = Field(default=[], description="标签名称列表")
    auto_summarize: bool = Field(default=True, description="是否自动生成摘要")
    auto_tag: bool = Field(default=True, description="是否自动生成标签")


class BookmarkUpdate(BaseModel):
    """更新收藏请求"""
    title: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[List[str]] = None


class BookmarkResponse(BaseModel):
    """收藏响应"""
    id: str
    title: str
    url: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    type: BookmarkType
    is_embedded: bool = False
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    tags: List[TagResponse] = []
    
    class Config:
        from_attributes = True


class BookmarkListResponse(BaseModel):
    """收藏列表响应"""
    items: List[BookmarkResponse]
    total: int
    page: int = 1
    page_size: int = 20
    has_more: bool = False


# ==================== 搜索模型 ====================

class SearchRequest(BaseModel):
    """搜索请求"""
    query: str = Field(..., min_length=1, description="搜索关键词")
    tags: List[str] = Field(default=[], description="标签筛选")
    type: Optional[BookmarkType] = Field(None, description="类型筛选")
    use_semantic: bool = Field(default=True, description="是否使用语义搜索")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class SearchResult(BaseModel):
    """搜索结果项"""
    bookmark: BookmarkResponse
    relevance: float = Field(..., ge=0, le=1, description="相关度分数")
    highlight: Optional[str] = None  # 高亮匹配的内容


class SearchResponse(BaseModel):
    """搜索响应"""
    results: List[SearchResult]
    total: int
    query: str
