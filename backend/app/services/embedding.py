"""
向量嵌入服务
使用真正的向量嵌入实现语义搜索
支持豆包 embedding API
"""

import os
import json
import httpx
import numpy as np
from typing import List, Dict, Optional
from pathlib import Path

from ..core.config import settings


class VectorStore:
    """
    向量存储
    使用 numpy 进行向量计算，JSON 文件持久化
    """
    
    def __init__(self, persist_dir: str, dimension: int = 2048):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.persist_dir / "vector_index.json"
        self.dimension = dimension
        self.documents: Dict[str, Dict] = {}
        self._load()
    
    def _load(self):
        """从文件加载索引"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.documents = data.get('documents', {})
            except Exception as e:
                print(f"加载向量索引失败: {e}")
                self.documents = {}
    
    def _save(self):
        """保存索引到文件"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump({'documents': self.documents}, f, ensure_ascii=False)
        except Exception as e:
            print(f"保存向量索引失败: {e}")
    
    def add(self, doc_id: str, content: str, embedding: List[float], metadata: Dict = None):
        """添加文档和向量"""
        self.documents[doc_id] = {
            'content': content,
            'embedding': embedding,
            'metadata': metadata or {}
        }
        self._save()
    
    def update(self, doc_id: str, content: str, embedding: List[float], metadata: Dict = None):
        """更新文档"""
        self.add(doc_id, content, embedding, metadata)
    
    def delete(self, doc_id: str):
        """删除文档"""
        if doc_id in self.documents:
            del self.documents[doc_id]
            self._save()
    
    def get(self, doc_id: str) -> Optional[Dict]:
        """获取文档"""
        return self.documents.get(doc_id)
    
    def search(self, query_embedding: List[float], n_results: int = 5) -> List[Dict]:
        """
        向量相似度搜索
        使用余弦相似度
        """
        if not self.documents:
            return []
        
        query_vec = np.array(query_embedding)
        query_norm = np.linalg.norm(query_vec)
        
        if query_norm == 0:
            return []
        
        results = []
        for doc_id, doc in self.documents.items():
            doc_embedding = doc.get('embedding', [])
            if not doc_embedding:
                continue
            
            doc_vec = np.array(doc_embedding)
            doc_norm = np.linalg.norm(doc_vec)
            
            if doc_norm == 0:
                continue
            
            # 余弦相似度
            similarity = np.dot(query_vec, doc_vec) / (query_norm * doc_norm)
            
            # 转换为 0-1 的相关度分数
            relevance = (similarity + 1) / 2  # 从 [-1,1] 映射到 [0,1]
            
            results.append({
                'id': doc_id,
                'content': doc.get('content'),
                'metadata': doc.get('metadata', {}),
                'relevance': float(relevance)
            })
        
        # 按相关度排序
        results.sort(key=lambda x: x['relevance'], reverse=True)
        return results[:n_results]
    
    def count(self) -> int:
        """获取文档数量"""
        return len(self.documents)


class EmbeddingClient:
    """
    Embedding API 客户端
    支持豆包多模态 embedding
    """
    
    def __init__(self):
        self.api_key = settings.doubao_api_key
        self.base_url = settings.doubao_base_url.rstrip('/')
        self.model = settings.doubao_embedding_model
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """
        获取文本的向量嵌入
        使用豆包多模态 embedding API
        
        Args:
            texts: 文本列表
        
        Returns:
            向量列表
        """
        # 使用多模态 embedding 接口
        url = f"{self.base_url}/embeddings/multimodal"
        
        embeddings = []
        for text in texts:
            payload = {
                "model": self.model,
                "input": [
                    {
                        "type": "text",
                        "text": text[:4000]  # 限制长度
                    }
                ]
            }
            
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(url, headers=self.headers, json=payload)
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"API 响应: {str(data)[:200]}...")  # 调试日志
                        
                        # 提取向量 - 支持多种格式
                        embedding = []
                        if data.get('data'):
                            data_field = data['data']
                            if isinstance(data_field, list) and len(data_field) > 0:
                                # 列表格式: [{"embedding": [...]}]
                                embedding = data_field[0].get('embedding', [])
                            elif isinstance(data_field, dict):
                                # 字典格式: {"embedding": [...]}
                                embedding = data_field.get('embedding', [])
                        elif data.get('embedding'):
                            # 直接返回 embedding
                            embedding = data['embedding']
                        
                        if embedding:
                            embeddings.append(embedding)
                            print(f"✓ 向量化成功，维度: {len(embedding)}")
                        else:
                            print(f"⚠ 向量化返回空 embedding，完整响应: {data}")
                            embeddings.append([])
                    else:
                        print(f"✗ Embedding API 失败 - 状态码: {response.status_code}, 响应: {response.text[:300]}")
                        embeddings.append([])
            except httpx.TimeoutException as e:
                print(f"✗ Embedding API 超时: {e}")
                embeddings.append([])
            except httpx.RequestError as e:
                print(f"✗ Embedding API 请求错误: {type(e).__name__}: {e}")
                embeddings.append([])
            except Exception as e:
                print(f"✗ Embedding API 调用异常: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                embeddings.append([])
        
        return embeddings
    
    async def embed_single(self, text: str) -> List[float]:
        """获取单个文本的向量"""
        results = await self.embed([text])
        return results[0] if results else []


class EmbeddingService:
    """
    向量嵌入服务
    结合 embedding API 和向量存储
    """
    
    COLLECTION_NAME = "knowledge_keeper"
    
    def __init__(self):
        """初始化向量存储和 embedding 客户端"""
        persist_dir = settings.chroma_persist_dir
        self.store = VectorStore(persist_dir, settings.embedding_dimension)
        self.client = EmbeddingClient()
        # 回退到简单搜索的标志
        self._use_fallback = False
    
    async def add_document(
        self,
        doc_id: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        添加文档到向量库
        """
        try:
            # 获取向量嵌入
            embedding = await self.client.embed_single(content[:4000])  # 限制长度
            
            if embedding:
                self.store.add(doc_id, content, embedding, metadata)
                return True
            else:
                # 如果 embedding 失败，使用简单存储
                print(f"Embedding 失败，使用简单存储")
                self.store.add(doc_id, content, [], metadata)
                self._use_fallback = True
                return True
        except Exception as e:
            print(f"添加文档失败: {e}")
            return False
    
    async def update_document(
        self,
        doc_id: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """更新文档"""
        return await self.add_document(doc_id, content, metadata)
    
    async def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        try:
            self.store.delete(doc_id)
            return True
        except Exception as e:
            print(f"删除文档失败: {e}")
            return False
    
    async def search(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        语义搜索
        """
        try:
            # 获取查询向量
            query_embedding = await self.client.embed_single(query)
            
            if query_embedding:
                results = self.store.search(query_embedding, n_results)
                # 过滤低相关度结果
                return [r for r in results if r['relevance'] > 0.5]
            else:
                # 回退到文本搜索
                return self._fallback_search(query, n_results)
        except Exception as e:
            print(f"搜索失败: {e}")
            return self._fallback_search(query, n_results)
    
    def _fallback_search(self, query: str, n_results: int = 5) -> List[Dict]:
        """
        回退的文本搜索（当 embedding 不可用时）
        """
        import re
        query_lower = query.lower()
        
        results = []
        for doc_id, doc in self.store.documents.items():
            content = doc.get('content', '').lower()
            metadata = doc.get('metadata', {})
            title = metadata.get('title', '').lower()
            
            score = 0.0
            
            # 完整查询匹配
            if query_lower in content:
                score += 0.6
            if query_lower in title:
                score += 0.3
            
            # 字符匹配
            query_chars = re.findall(r'[\u4e00-\u9fff]', query)
            if query_chars:
                matching = sum(1 for c in query_chars if c in content)
                score += (matching / len(query_chars)) * 0.4
            
            if score > 0.2:
                results.append({
                    'id': doc_id,
                    'content': doc.get('content'),
                    'metadata': metadata,
                    'relevance': min(score, 1.0)
                })
        
        results.sort(key=lambda x: x['relevance'], reverse=True)
        return results[:n_results]
    
    async def get_document(self, doc_id: str) -> Optional[Dict]:
        """获取单个文档"""
        doc = self.store.get(doc_id)
        if doc:
            return {
                'id': doc_id,
                'content': doc.get('content'),
                'metadata': doc.get('metadata', {})
            }
        return None
    
    def get_collection_stats(self) -> Dict:
        """获取集合统计信息"""
        return {
            'name': self.COLLECTION_NAME,
            'count': self.store.count(),
            'using_embeddings': not self._use_fallback
        }
    
    async def clear_all(self) -> bool:
        """清空所有文档"""
        try:
            self.store.documents = {}
            self.store._save()
            return True
        except Exception as e:
            print(f"清空失败: {e}")
            return False


# 全局单例
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """获取嵌入服务单例"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
