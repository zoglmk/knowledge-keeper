"""
收藏相关 API
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from ..core.database import get_db
from ..models.bookmark import Bookmark, Tag, BookmarkTag, BookmarkType
from ..schemas.bookmark import (
    BookmarkCreate, BookmarkUpdate, BookmarkResponse, 
    BookmarkListResponse, TagResponse
)
from ..services.scraper import WebScraper
from ..services.ai_service import AIService
from ..services.embedding import get_embedding_service

router = APIRouter(prefix="/bookmarks", tags=["收藏"])


@router.get("", response_model=BookmarkListResponse)
async def list_bookmarks(
    page: int = 1,
    page_size: int = 20,
    tag: Optional[str] = None,
    type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取收藏列表"""
    # 构建查询
    query = select(Bookmark).where(Bookmark.is_active == True)
    
    # 标签筛选
    if tag:
        query = query.join(BookmarkTag).join(Tag).where(Tag.name == tag)
    
    # 类型筛选
    if type:
        try:
            bookmark_type = BookmarkType(type)
            query = query.where(Bookmark.type == bookmark_type)
        except ValueError:
            pass
    
    # 添加关联加载
    query = query.options(selectinload(Bookmark.tags))
    
    # 排序
    query = query.order_by(desc(Bookmark.created_at))
    
    # 计算总数
    count_query = select(func.count()).select_from(
        select(Bookmark.id).where(Bookmark.is_active == True).subquery()
    )
    if tag:
        count_query = select(func.count()).select_from(
            select(Bookmark.id)
            .join(BookmarkTag)
            .join(Tag)
            .where(Bookmark.is_active == True, Tag.name == tag)
            .subquery()
        )
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 分页
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    bookmarks = result.scalars().unique().all()
    
    return BookmarkListResponse(
        items=[BookmarkResponse.model_validate(b) for b in bookmarks],
        total=total,
        page=page,
        page_size=page_size,
        has_more=offset + len(bookmarks) < total
    )


@router.post("", response_model=BookmarkResponse)
async def create_bookmark(
    data: BookmarkCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建新收藏
    
    - 如果是 URL 类型，会自动抓取网页内容
    - 如果开启 auto_summarize，会自动生成摘要
    - 如果开启 auto_tag，会自动生成标签
    """
    title = data.title
    content = data.content
    
    # URL 类型：抓取网页内容
    if data.type == "url" and data.url:
        scraper = WebScraper()
        scraped = await scraper.fetch(data.url)
        
        if scraped.get('error'):
            # 抓取失败，使用用户提供的数据
            if not title:
                title = data.url
        else:
            if not title:
                title = scraped.get('title') or data.url
            if not content:
                content = scraped.get('content') or scraped.get('description') or ""
    
    # 确保有标题
    if not title:
        title = "未命名收藏"
    
    # 创建收藏对象
    bookmark = Bookmark(
        title=title,
        url=data.url,
        content=content,
        type=BookmarkType(data.type),
    )
    
    # 自动生成摘要
    if data.auto_summarize and content:
        try:
            ai_service = AIService()
            summary = await ai_service.summarize(content)
            bookmark.summary = summary
        except Exception as e:
            print(f"生成摘要失败: {e}")
    
    # 处理标签
    all_tag_names = list(data.tags)  # 用户指定的标签
    
    # 自动生成标签
    if data.auto_tag and content:
        try:
            ai_service = AIService()
            # 获取已有标签名称供 AI 参考
            existing_tags_query = select(Tag.name).limit(50)
            existing_result = await db.execute(existing_tags_query)
            existing_tag_names = [row[0] for row in existing_result.fetchall()]
            
            auto_tags = await ai_service.generate_tags(content, existing_tag_names)
            all_tag_names.extend(auto_tags)
        except Exception as e:
            print(f"生成标签失败: {e}")
    
    # 去重
    all_tag_names = list(set(all_tag_names))
    
    # 获取或创建标签
    for tag_name in all_tag_names:
        if not tag_name.strip():
            continue
        
        # 查找已有标签
        tag_query = select(Tag).where(Tag.name == tag_name.strip())
        tag_result = await db.execute(tag_query)
        tag = tag_result.scalar_one_or_none()
        
        if not tag:
            # 创建新标签
            tag = Tag(
                name=tag_name.strip(),
                is_auto=tag_name not in data.tags  # 标记是否为自动生成
            )
            db.add(tag)
        
        bookmark.tags.append(tag)
    
    db.add(bookmark)
    await db.commit()
    await db.refresh(bookmark)
    
    # 添加到向量库
    if content:
        try:
            embedding_service = get_embedding_service()
            await embedding_service.add_document(
                doc_id=bookmark.id,
                content=content,
                metadata={
                    'title': bookmark.title,
                    'url': bookmark.url,
                    'type': bookmark.type.value
                }
            )
            bookmark.is_embedded = True
            await db.commit()
        except Exception as e:
            print(f"向量化失败: {e}")
    
    return BookmarkResponse.model_validate(bookmark)


@router.get("/{bookmark_id}", response_model=BookmarkResponse)
async def get_bookmark(
    bookmark_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取收藏详情"""
    query = select(Bookmark).where(
        Bookmark.id == bookmark_id,
        Bookmark.is_active == True
    ).options(selectinload(Bookmark.tags))
    
    result = await db.execute(query)
    bookmark = result.scalar_one_or_none()
    
    if not bookmark:
        raise HTTPException(status_code=404, detail="收藏不存在")
    
    return BookmarkResponse.model_validate(bookmark)


@router.put("/{bookmark_id}", response_model=BookmarkResponse)
async def update_bookmark(
    bookmark_id: str,
    data: BookmarkUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新收藏"""
    query = select(Bookmark).where(
        Bookmark.id == bookmark_id,
        Bookmark.is_active == True
    ).options(selectinload(Bookmark.tags))
    
    result = await db.execute(query)
    bookmark = result.scalar_one_or_none()
    
    if not bookmark:
        raise HTTPException(status_code=404, detail="收藏不存在")
    
    # 更新字段
    if data.title is not None:
        bookmark.title = data.title
    if data.content is not None:
        bookmark.content = data.content
    if data.summary is not None:
        bookmark.summary = data.summary
    
    # 更新标签
    if data.tags is not None:
        # 清除现有标签关联
        bookmark.tags.clear()
        
        # 添加新标签
        for tag_name in data.tags:
            if not tag_name.strip():
                continue
            
            tag_query = select(Tag).where(Tag.name == tag_name.strip())
            tag_result = await db.execute(tag_query)
            tag = tag_result.scalar_one_or_none()
            
            if not tag:
                tag = Tag(name=tag_name.strip())
                db.add(tag)
            
            bookmark.tags.append(tag)
    
    await db.commit()
    await db.refresh(bookmark)
    
    # 更新向量库
    if bookmark.content:
        try:
            embedding_service = get_embedding_service()
            await embedding_service.update_document(
                doc_id=bookmark.id,
                content=bookmark.content,
                metadata={
                    'title': bookmark.title,
                    'url': bookmark.url,
                    'type': bookmark.type.value
                }
            )
        except Exception as e:
            print(f"更新向量失败: {e}")
    
    return BookmarkResponse.model_validate(bookmark)


@router.delete("/{bookmark_id}")
async def delete_bookmark(
    bookmark_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除收藏（软删除）并清理无用标签"""
    query = select(Bookmark).where(
        Bookmark.id == bookmark_id,
        Bookmark.is_active == True
    ).options(selectinload(Bookmark.tags))
    
    result = await db.execute(query)
    bookmark = result.scalar_one_or_none()
    
    if not bookmark:
        raise HTTPException(status_code=404, detail="收藏不存在")
    
    # 记录当前收藏的标签 ID，用于后续清理
    tag_ids_to_check = [tag.id for tag in bookmark.tags]
    
    # 软删除 - 清除标签关联并标记为非活跃
    bookmark.tags.clear()  # 先清除标签关联
    bookmark.is_active = False
    await db.commit()
    
    # 检查并删除不再被使用的标签
    if tag_ids_to_check:
        for tag_id in tag_ids_to_check:
            # 检查这个标签是否还被其他活跃的收藏使用
            usage_query = (
                select(func.count(BookmarkTag.c.bookmark_id))
                .select_from(BookmarkTag)
                .join(Bookmark, BookmarkTag.c.bookmark_id == Bookmark.id)
                .where(
                    BookmarkTag.c.tag_id == tag_id,
                    Bookmark.is_active == True
                )
            )
            usage_result = await db.execute(usage_query)
            usage_count = usage_result.scalar() or 0
            
            # 如果没有其他收藏使用这个标签，则删除它
            if usage_count == 0:
                tag_query = select(Tag).where(Tag.id == tag_id)
                tag_result = await db.execute(tag_query)
                tag = tag_result.scalar_one_or_none()
                if tag:
                    await db.delete(tag)
        
        await db.commit()
    
    # 从向量库删除
    try:
        embedding_service = get_embedding_service()
        await embedding_service.delete_document(bookmark_id)
    except Exception as e:
        print(f"删除向量失败: {e}")
    
    return {"message": "删除成功"}


@router.post("/{bookmark_id}/regenerate-summary", response_model=BookmarkResponse)
async def regenerate_summary(
    bookmark_id: str,
    db: AsyncSession = Depends(get_db)
):
    """重新生成摘要和标签"""
    query = select(Bookmark).where(
        Bookmark.id == bookmark_id,
        Bookmark.is_active == True
    ).options(selectinload(Bookmark.tags))
    
    result = await db.execute(query)
    bookmark = result.scalar_one_or_none()
    
    if not bookmark:
        raise HTTPException(status_code=404, detail="收藏不存在")
    
    if not bookmark.content:
        raise HTTPException(status_code=400, detail="没有可用于生成摘要的内容")
    
    try:
        ai_service = AIService()
        
        # 重新生成摘要
        summary = await ai_service.summarize(bookmark.content)
        bookmark.summary = summary
        
        # 重新生成标签
        tag_names = await ai_service.generate_tags(bookmark.content)
        
        # 清除旧标签关联
        bookmark.tags.clear()
        
        # 创建或获取新标签
        for tag_name in tag_names:
            if not tag_name or len(tag_name) > 20:
                continue
            # 查找或创建标签
            tag_query = select(Tag).where(Tag.name == tag_name)
            tag_result = await db.execute(tag_query)
            tag = tag_result.scalar_one_or_none()
            
            if not tag:
                tag = Tag(
                    name=tag_name,
                    is_auto=True,
                    color="#6366f1"
                )
                db.add(tag)
            
            bookmark.tags.append(tag)
        
        await db.commit()
        await db.refresh(bookmark)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")
    
    return BookmarkResponse.model_validate(bookmark)


@router.post("/reindex-all")
async def reindex_all_bookmarks(
    db: AsyncSession = Depends(get_db)
):
    """重新索引所有收藏到向量库"""
    # 获取所有活跃的收藏
    query = select(Bookmark).where(Bookmark.is_active == True)
    result = await db.execute(query)
    bookmarks = result.scalars().all()
    
    embedding_service = get_embedding_service()
    success_count = 0
    fail_count = 0
    
    for bookmark in bookmarks:
        if bookmark.content:
            try:
                await embedding_service.add_document(
                    doc_id=bookmark.id,
                    content=bookmark.content,
                    metadata={
                        'title': bookmark.title,
                        'url': bookmark.url,
                        'type': bookmark.type.value
                    }
                )
                bookmark.is_embedded = True
                success_count += 1
            except Exception as e:
                print(f"重新索引 {bookmark.id} 失败: {e}")
                fail_count += 1
    
    await db.commit()
    
    return {
        "message": f"重新索引完成",
        "success": success_count,
        "failed": fail_count,
        "total": len(bookmarks)
    }


def parse_file_content(filename: str, content: bytes, content_type: str) -> str:
    """解析文件内容"""
    filename_lower = filename.lower() if filename else ""
    
    # 文本文件
    if "text" in content_type or filename_lower.endswith(('.txt', '.md', '.markdown')):
        try:
            return content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                return content.decode('gbk')
            except UnicodeDecodeError:
                return content.decode('latin-1', errors='ignore')
    
    # PDF 文件
    elif filename_lower.endswith('.pdf'):
        try:
            from PyPDF2 import PdfReader
            import io
            reader = PdfReader(io.BytesIO(content))
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            return "\n\n".join(text_parts)
        except Exception as e:
            return f"[PDF 解析失败: {e}]"
    
    # Word 文档
    elif filename_lower.endswith(('.docx', '.doc')):
        try:
            from docx import Document
            import io
            doc = Document(io.BytesIO(content))
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            return "\n\n".join(paragraphs)
        except Exception as e:
            return f"[Word 文档解析失败: {e}]"
    
    # HTML 文件
    elif filename_lower.endswith(('.html', '.htm')):
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            # 移除脚本和样式
            for script in soup(["script", "style"]):
                script.decompose()
            return soup.get_text(separator='\n', strip=True)
        except Exception as e:
            return f"[HTML 解析失败: {e}]"
    
    # JSON 文件
    elif filename_lower.endswith('.json'):
        try:
            import json
            data = json.loads(content.decode('utf-8'))
            return json.dumps(data, indent=2, ensure_ascii=False)
        except Exception as e:
            return f"[JSON 解析失败: {e}]"
    
    else:
        return f"[不支持的文件类型: {content_type}]"


@router.post("/upload", response_model=BookmarkResponse)
async def upload_file(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    tags: str = Form(""),
    auto_summarize: bool = Form(True),
    auto_tag: bool = Form(True),
    db: AsyncSession = Depends(get_db)
):
    """上传单个文件创建收藏"""
    content = await file.read()
    file_content = parse_file_content(
        file.filename or "unknown",
        content,
        file.content_type or ""
    )
    
    tag_list = [t.strip() for t in tags.split(',') if t.strip()]
    
    bookmark_data = BookmarkCreate(
        title=title or file.filename or "未命名文件",
        content=file_content,
        type="file",
        tags=tag_list,
        auto_summarize=auto_summarize,
        auto_tag=auto_tag
    )
    
    return await create_bookmark(bookmark_data, db)


@router.post("/upload/batch", response_model=List[BookmarkResponse])
async def upload_files_batch(
    files: List[UploadFile] = File(...),
    auto_summarize: bool = Form(True),
    auto_tag: bool = Form(True),
    db: AsyncSession = Depends(get_db)
):
    """批量上传多个文件"""
    results = []
    
    for file in files:
        try:
            content = await file.read()
            file_content = parse_file_content(
                file.filename or "unknown",
                content,
                file.content_type or ""
            )
            
            bookmark_data = BookmarkCreate(
                title=file.filename or "未命名文件",
                content=file_content,
                type="file",
                tags=[],
                auto_summarize=auto_summarize,
                auto_tag=auto_tag
            )
            
            bookmark = await create_bookmark(bookmark_data, db)
            results.append(bookmark)
        except Exception as e:
            print(f"上传文件 {file.filename} 失败: {e}")
            continue
    
    return results

