"""
标签相关 API
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from ..core.database import get_db
from ..models.bookmark import Tag, BookmarkTag
from ..schemas.bookmark import TagCreate, TagResponse

router = APIRouter(prefix="/tags", tags=["标签"])


@router.get("", response_model=List[TagResponse])
async def list_tags(
    db: AsyncSession = Depends(get_db)
):
    """获取所有标签"""
    query = select(Tag).order_by(desc(Tag.created_at))
    result = await db.execute(query)
    tags = result.scalars().all()
    
    return [TagResponse.model_validate(t) for t in tags]


@router.get("/popular", response_model=List[TagResponse])
async def get_popular_tags(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """获取热门标签（按使用次数排序）"""
    # 统计每个标签的使用次数
    query = (
        select(Tag, func.count(BookmarkTag.c.bookmark_id).label('count'))
        .outerjoin(BookmarkTag, Tag.id == BookmarkTag.c.tag_id)
        .group_by(Tag.id)
        .order_by(desc('count'))
        .limit(limit)
    )
    
    result = await db.execute(query)
    tags_with_count = result.all()
    
    return [TagResponse.model_validate(t[0]) for t in tags_with_count]


@router.post("", response_model=TagResponse)
async def create_tag(
    data: TagCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建新标签"""
    # 检查是否已存在
    query = select(Tag).where(Tag.name == data.name.strip())
    result = await db.execute(query)
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="标签已存在")
    
    tag = Tag(
        name=data.name.strip(),
        color=data.color,
        is_auto=False
    )
    
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    
    return TagResponse.model_validate(tag)


@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: str,
    data: TagCreate,
    db: AsyncSession = Depends(get_db)
):
    """更新标签"""
    query = select(Tag).where(Tag.id == tag_id)
    result = await db.execute(query)
    tag = result.scalar_one_or_none()
    
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    
    # 检查名称是否冲突
    if data.name.strip() != tag.name:
        check_query = select(Tag).where(Tag.name == data.name.strip())
        check_result = await db.execute(check_query)
        if check_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="标签名称已存在")
    
    tag.name = data.name.strip()
    tag.color = data.color
    
    await db.commit()
    await db.refresh(tag)
    
    return TagResponse.model_validate(tag)


@router.delete("/{tag_id}")
async def delete_tag(
    tag_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除标签"""
    query = select(Tag).where(Tag.id == tag_id)
    result = await db.execute(query)
    tag = result.scalar_one_or_none()
    
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    
    await db.delete(tag)
    await db.commit()
    
    return {"message": "删除成功"}
