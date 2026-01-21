"""
RAG (Retrieval-Augmented Generation) 服务
结合向量检索和 AI 生成来回答问题
"""

from typing import List, Dict, Optional
from .embedding import get_embedding_service, EmbeddingService
from .ai_service import AIService


class RAGService:
    """
    RAG 服务
    1. 从向量库中检索相关文档
    2. 将检索到的文档作为上下文
    3. 使用 AI 生成回答
    """
    
    def __init__(self, ai_provider: Optional[str] = None):
        """
        初始化 RAG 服务
        
        Args:
            ai_provider: AI 提供商，默认使用配置文件中的设置
        """
        self.embedding_service = get_embedding_service()
        self.ai_service = AIService(provider=ai_provider)
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        min_relevance: float = 0.3
    ) -> List[Dict]:
        """
        检索相关文档
        
        Args:
            query: 查询文本
            top_k: 返回的最大文档数
            min_relevance: 最小相关度阈值
        
        Returns:
            相关文档列表
        """
        results = await self.embedding_service.search(query, n_results=top_k)
        
        # 过滤低相关度的结果
        filtered = [r for r in results if r.get('relevance', 0) >= min_relevance]
        
        return filtered
    
    async def generate_answer(
        self,
        question: str,
        context_docs: List[Dict],
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        基于上下文生成回答
        
        Args:
            question: 用户问题
            context_docs: 相关文档列表
            conversation_history: 对话历史
        
        Returns:
            AI 生成的回答
        """
        # 准备上下文
        context = []
        for doc in context_docs:
            metadata = doc.get('metadata', {})
            context.append({
                'title': metadata.get('title', '未命名文档'),
                'content': doc.get('content', '')
            })
        
        # 使用 AI 服务生成回答
        answer = await self.ai_service.answer_with_context(
            question=question,
            context=context,
            conversation_history=conversation_history
        )
        
        return answer
    
    async def chat(
        self,
        question: str,
        conversation_history: Optional[List[Dict]] = None,
        use_knowledge_base: bool = True,
        top_k: int = 5
    ) -> Dict:
        """
        RAG 聊天
        
        Args:
            question: 用户问题
            conversation_history: 对话历史
            use_knowledge_base: 是否使用知识库
            top_k: 检索的文档数量
        
        Returns:
            包含 answer 和 sources 的字典
        """
        sources = []
        context_docs = []
        
        if use_knowledge_base:
            # 检索相关文档
            context_docs = await self.retrieve(question, top_k=top_k)
            
            # 提取来源信息
            for doc in context_docs:
                metadata = doc.get('metadata', {})
                sources.append({
                    'bookmark_id': doc['id'],
                    'title': metadata.get('title', '未命名'),
                    'url': metadata.get('url'),
                    'relevance': doc.get('relevance', 0),
                    'snippet': (doc.get('content', '')[:200] + '...') if doc.get('content') else None
                })
        
        # 生成回答
        if context_docs or not use_knowledge_base:
            answer = await self.generate_answer(
                question=question,
                context_docs=context_docs,
                conversation_history=conversation_history
            )
        else:
            # 知识库中没有相关内容
            answer = "很抱歉，我在您的知识库中没有找到相关信息。您可以尝试添加更多相关内容，或者换一种方式提问。"
        
        return {
            'answer': answer,
            'sources': sources
        }
    
    async def summarize_results(self, query: str, results: List[Dict]) -> str:
        """
        对搜索结果进行总结
        
        Args:
            query: 原始查询
            results: 搜索结果列表
        
        Returns:
            总结文本
        """
        if not results:
            return "没有找到相关结果。"
        
        # 构建上下文
        context_text = "\n\n".join([
            f"【{r.get('metadata', {}).get('title', '未命名')}】\n{r.get('content', '')[:500]}"
            for r in results[:5]
        ])
        
        messages = [
            {
                "role": "system",
                "content": f"请根据以下搜索结果，针对用户的查询'{query}'生成一个简洁的总结。用中文回答。"
            },
            {
                "role": "user",
                "content": f"搜索结果：\n{context_text}"
            }
        ]
        
        return await self.ai_service.chat(messages)


# 全局单例
_rag_service: Optional[RAGService] = None


def get_rag_service(ai_provider: Optional[str] = None) -> RAGService:
    """获取 RAG 服务"""
    global _rag_service
    if _rag_service is None or ai_provider:
        _rag_service = RAGService(ai_provider=ai_provider)
    return _rag_service
