"""
对话相关 API
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
import json

from ..core.database import get_db
from ..models.conversation import Conversation, Message, MessageRole
from ..schemas.conversation import (
    ConversationCreate, ConversationResponse, ConversationListResponse,
    MessageResponse, ChatRequest, ChatResponse, SourceReference
)
from ..services.rag import get_rag_service

router = APIRouter(prefix="/chat", tags=["对话"])


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    db: AsyncSession = Depends(get_db)
):
    """获取对话列表"""
    query = (
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .order_by(desc(Conversation.updated_at))
    )
    
    result = await db.execute(query)
    conversations = result.scalars().unique().all()
    
    response_items = []
    for conv in conversations:
        conv_response = ConversationResponse.model_validate(conv)
        conv_response.message_count = len(conv.messages)
        response_items.append(conv_response)
    
    return ConversationListResponse(
        items=response_items,
        total=len(response_items)
    )


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    data: ConversationCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建新对话"""
    conversation = Conversation(title=data.title)
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    
    return ConversationResponse.model_validate(conversation)


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取对话详情"""
    query = (
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(selectinload(Conversation.messages))
    )
    
    result = await db.execute(query)
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    response = ConversationResponse.model_validate(conversation)
    response.message_count = len(conversation.messages)
    
    return response


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除对话"""
    query = select(Conversation).where(Conversation.id == conversation_id)
    result = await db.execute(query)
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    await db.delete(conversation)
    await db.commit()
    
    return {"message": "删除成功"}


@router.post("", response_model=ChatResponse)
async def chat(
    data: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    发送消息并获取 AI 回复
    
    - 如果 conversation_id 为空，会自动创建新对话
    - 如果 use_knowledge_base 为 True，会从知识库中检索相关内容
    """
    conversation = None
    conversation_history = []
    
    # 获取或创建对话
    if data.conversation_id:
        query = (
            select(Conversation)
            .where(Conversation.id == data.conversation_id)
            .options(selectinload(Conversation.messages))
        )
        result = await db.execute(query)
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
        
        # 构建对话历史
        for msg in conversation.messages:
            conversation_history.append({
                "role": msg.role.value,
                "content": msg.content
            })
    else:
        # 创建新对话
        conversation = Conversation(title=data.message[:50] + "..." if len(data.message) > 50 else data.message)
        db.add(conversation)
        await db.flush()  # 获取 ID
    
    # 保存用户消息
    user_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content=data.message
    )
    db.add(user_message)
    
    # 使用 RAG 服务获取回复
    rag_service = get_rag_service()
    rag_result = await rag_service.chat(
        question=data.message,
        conversation_history=conversation_history,
        use_knowledge_base=data.use_knowledge_base
    )
    
    # 构建来源引用
    sources_json = None
    sources_response = []
    
    if rag_result['sources']:
        sources_json = rag_result['sources']
        sources_response = [
            SourceReference(
                bookmark_id=s['bookmark_id'],
                title=s['title'],
                url=s.get('url'),
                relevance=s['relevance'],
                snippet=s.get('snippet')
            )
            for s in rag_result['sources']
        ]
    
    # 保存 AI 回复
    assistant_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.ASSISTANT,
        content=rag_result['answer'],
        sources=sources_json
    )
    db.add(assistant_message)
    
    await db.commit()
    await db.refresh(assistant_message)
    
    return ChatResponse(
        conversation_id=conversation.id,
        message=MessageResponse.model_validate(assistant_message),
        sources=sources_response
    )


@router.post("/stream")
async def chat_stream(
    data: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    流式对话（SSE）
    
    返回 Server-Sent Events 流
    """
    conversation = None
    conversation_history = []
    
    # 获取或创建对话
    if data.conversation_id:
        query = (
            select(Conversation)
            .where(Conversation.id == data.conversation_id)
            .options(selectinload(Conversation.messages))
        )
        result = await db.execute(query)
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
        
        for msg in conversation.messages:
            conversation_history.append({
                "role": msg.role.value,
                "content": msg.content
            })
    else:
        conversation = Conversation(title=data.message[:50] + "..." if len(data.message) > 50 else data.message)
        db.add(conversation)
        await db.flush()
    
    # 保存用户消息并提交，使对话立即出现在列表中
    user_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content=data.message
    )
    db.add(user_message)
    await db.commit()  # 立即提交，对话会出现在列表中
    await db.refresh(conversation)  # 刷新获取最新状态
    
    async def generate():
        rag_service = get_rag_service()
        
        # 先检索相关文档
        sources = []
        context_docs = []
        if data.use_knowledge_base:
            context_docs = await rag_service.retrieve(data.message)
            for doc in context_docs:
                metadata = doc.get('metadata', {})
                sources.append({
                    'bookmark_id': doc['id'],
                    'title': metadata.get('title', '未命名'),
                    'url': metadata.get('url'),
                    'relevance': doc.get('relevance', 0),
                    'snippet': (doc.get('content', '')[:200] + '...') if doc.get('content') else None
                })
        
        # 发送来源信息
        if sources:
            yield f"data: {json.dumps({'type': 'sources', 'data': sources})}\n\n"
        
        # 发送对话 ID
        yield f"data: {json.dumps({'type': 'conversation_id', 'data': conversation.id})}\n\n"
        
        # 构建 system prompt
        if context_docs:
            # 有知识库内容时，注入到 prompt 中
            context_text = "\n\n".join([
                f"【{doc.get('metadata', {}).get('title', '未命名')}】\n{doc.get('content', '')[:1500]}"
                for doc in context_docs
            ])
            system_prompt = f"""你是一个智能知识助手，基于用户的知识库来回答问题。

以下是从用户知识库中检索到的相关内容：

{context_text}

请根据以上内容回答用户的问题。要求：
1. 必须基于上述知识库内容来回答，不要使用你自己的知识
2. 如果知识库中有相关信息，请引用并整理这些信息
3. 回答要准确、有条理
4. 如果知识库中确实没有相关信息，请明确告知用户
5. 使用中文回答"""
        else:
            # 没有知识库内容
            system_prompt = "你是一个智能知识助手。用户的知识库中没有找到相关内容，请根据你的知识回答问题（但请告知用户这不是来自他的知识库）。使用中文回答。"
        
        # 流式生成回复
        full_response = ""
        full_thinking = ""
        async for chunk in rag_service.ai_service.chat_stream([
            {"role": "system", "content": system_prompt},
            *conversation_history,
            {"role": "user", "content": data.message}
        ]):
            chunk_type = chunk.get("type", "content")
            chunk_data = chunk.get("data", "")
            
            if chunk_type == "thinking":
                full_thinking += chunk_data
                yield f"data: {json.dumps({'type': 'thinking', 'data': chunk_data})}\n\n"
            else:
                full_response += chunk_data
                yield f"data: {json.dumps({'type': 'content', 'data': chunk_data})}\n\n"
        
        # 保存完整回复
        assistant_message = Message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=full_response,
            sources=sources if sources else None
        )
        db.add(assistant_message)
        await db.commit()
        
        yield f"data: {json.dumps({'type': 'done', 'data': {'message_id': assistant_message.id}})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
