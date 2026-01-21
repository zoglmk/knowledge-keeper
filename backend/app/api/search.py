"""
搜索相关 API
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, desc
from sqlalchemy.orm import selectinload

from ..core.database import get_db
from ..models.bookmark import Bookmark, Tag, BookmarkTag
from ..schemas.bookmark import (
    SearchRequest, SearchResponse, SearchResult, BookmarkResponse
)
from ..services.embedding import get_embedding_service

router = APIRouter(prefix="/search", tags=["搜索"])


@router.get("", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    tags: Optional[str] = Query(None, description="标签过滤，多个标签用逗号分隔"),
    type: Optional[str] = Query(None, description="类型过滤"),
    use_semantic: bool = Query(True, description="是否使用语义搜索"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    搜索收藏
    
    - 支持关键词搜索和语义搜索
    - 可以按标签和类型过滤
    """
    results = []
    
    if use_semantic:
        # 语义搜索
        embedding_service = get_embedding_service()
        semantic_results = await embedding_service.search(
            query=q,
            n_results=page_size * 2  # 多取一些用于过滤
        )
        
        # 获取详细信息
        bookmark_ids = [r['id'] for r in semantic_results]
        
        if bookmark_ids:
            query = (
                select(Bookmark)
                .where(
                    Bookmark.id.in_(bookmark_ids),
                    Bookmark.is_active == True
                )
                .options(selectinload(Bookmark.tags))
            )
            
            db_result = await db.execute(query)
            bookmarks = {b.id: b for b in db_result.scalars().unique().all()}
            
            # 按标签过滤
            tag_list = [t.strip() for t in (tags or "").split(',') if t.strip()]
            
            for sem_result in semantic_results:
                bookmark = bookmarks.get(sem_result['id'])
                if not bookmark:
                    continue
                
                # 标签过滤
                if tag_list:
                    bookmark_tags = [t.name for t in bookmark.tags]
                    if not any(t in bookmark_tags for t in tag_list):
                        continue
                
                # 类型过滤
                if type and bookmark.type.value != type:
                    continue
                
                results.append(SearchResult(
                    bookmark=BookmarkResponse.model_validate(bookmark),
                    relevance=sem_result.get('relevance', 0.5),
                    highlight=sem_result.get('content', '')[:200] if sem_result.get('content') else None
                ))
    else:
        # 关键词搜索
        query = (
            select(Bookmark)
            .where(
                Bookmark.is_active == True,
                or_(
                    Bookmark.title.ilike(f"%{q}%"),
                    Bookmark.content.ilike(f"%{q}%"),
                    Bookmark.summary.ilike(f"%{q}%")
                )
            )
            .options(selectinload(Bookmark.tags))
            .order_by(desc(Bookmark.created_at))
        )
        
        # 标签过滤
        tag_list = [t.strip() for t in (tags or "").split(',') if t.strip()]
        if tag_list:
            query = query.join(BookmarkTag).join(Tag).where(Tag.name.in_(tag_list))
        
        # 类型过滤
        if type:
            from ..models.bookmark import BookmarkType
            try:
                bookmark_type = BookmarkType(type)
                query = query.where(Bookmark.type == bookmark_type)
            except ValueError:
                pass
        
        db_result = await db.execute(query)
        bookmarks = db_result.scalars().unique().all()
        
        for bookmark in bookmarks:
            # 简单的相关度计算
            relevance = 0.5
            if q.lower() in (bookmark.title or "").lower():
                relevance = 0.9
            elif q.lower() in (bookmark.summary or "").lower():
                relevance = 0.7
            
            # 高亮匹配
            highlight = None
            if bookmark.content and q.lower() in bookmark.content.lower():
                idx = bookmark.content.lower().find(q.lower())
                start = max(0, idx - 50)
                end = min(len(bookmark.content), idx + len(q) + 150)
                highlight = "..." + bookmark.content[start:end] + "..."
            
            results.append(SearchResult(
                bookmark=BookmarkResponse.model_validate(bookmark),
                relevance=relevance,
                highlight=highlight
            ))
    
    # 分页
    offset = (page - 1) * page_size
    paginated_results = results[offset:offset + page_size]
    
    return SearchResponse(
        results=paginated_results,
        total=len(results),
        query=q
    )


@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db)
):
    """获取统计信息"""
    from sqlalchemy import func
    from ..models.bookmark import BookmarkType
    
    # 总数
    total_query = select(func.count()).where(Bookmark.is_active == True)
    total_result = await db.execute(total_query)
    total = total_result.scalar() or 0
    
    # 按类型统计
    type_stats = {}
    for bt in BookmarkType:
        type_query = select(func.count()).where(
            Bookmark.is_active == True,
            Bookmark.type == bt
        )
        type_result = await db.execute(type_query)
        type_stats[bt.value] = type_result.scalar() or 0
    
    # 标签总数
    tag_count_query = select(func.count()).select_from(Tag)
    tag_result = await db.execute(tag_count_query)
    tag_count = tag_result.scalar() or 0
    
    # 已向量化的数量
    embedded_query = select(func.count()).where(
        Bookmark.is_active == True,
        Bookmark.is_embedded == True
    )
    embedded_result = await db.execute(embedded_query)
    embedded_count = embedded_result.scalar() or 0
    
    # 向量库统计
    embedding_service = get_embedding_service()
    vector_stats = embedding_service.get_collection_stats()
    
    return {
        "total_bookmarks": total,
        "by_type": type_stats,
        "total_tags": tag_count,
        "embedded_count": embedded_count,
        "vector_collection": vector_stats
    }
