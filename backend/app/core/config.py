"""
应用配置管理
支持多种 AI 模型提供商的配置
"""

from typing import Literal
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置类"""
    
    # 数据库配置
    database_url: str = "sqlite+aiosqlite:///./knowledge_keeper.db"
    
    # ChromaDB 配置
    chroma_persist_dir: str = "./chroma_data"
    
    # AI 模型提供商选择
    # 支持: openai, claude, gemini, doubao, deepseek
    ai_provider: Literal["openai", "claude", "gemini", "doubao", "deepseek"] = "doubao"
    
    # OpenAI 配置
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4"
    
    # Claude 配置
    claude_api_key: str = ""
    claude_base_url: str = "https://api.anthropic.com"
    claude_model: str = "claude-3-sonnet-20240229"
    
    # Gemini 配置
    gemini_api_key: str = ""
    gemini_model: str = "gemini-pro"
    
    # 豆包配置 (字节跳动火山引擎)
    doubao_api_key: str = ""
    doubao_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    doubao_model: str = "doubao-pro-4k"
    
    # Deepseek 配置
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"
    
    # 应用配置
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    
    # 嵌入模型配置 (用于向量化)
    # 支持: auto (跟随 ai_provider), openai, doubao
    embedding_provider: Literal["auto", "openai", "doubao"] = "auto"
    
    # OpenAI embedding 配置
    openai_embedding_model: str = "text-embedding-3-small"
    openai_embedding_dimension: int = 1536
    
    # 豆包多模态 embedding 模型
    doubao_embedding_model: str = "doubao-embedding-vision-250615"
    doubao_embedding_dimension: int = 3072
    
    # 默认 embedding 维度（根据实际使用的提供商动态调整）
    embedding_dimension: int = 2048
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def get_ai_config(self) -> dict:
        """获取当前 AI 提供商的配置"""
        provider_configs = {
            "openai": {
                "api_key": self.openai_api_key,
                "base_url": self.openai_base_url,
                "model": self.openai_model,
            },
            "claude": {
                "api_key": self.claude_api_key,
                "base_url": self.claude_base_url,
                "model": self.claude_model,
            },
            "gemini": {
                "api_key": self.gemini_api_key,
                "model": self.gemini_model,
            },
            "doubao": {
                "api_key": self.doubao_api_key,
                "base_url": self.doubao_base_url,
                "model": self.doubao_model,
            },
            "deepseek": {
                "api_key": self.deepseek_api_key,
                "base_url": self.deepseek_base_url,
                "model": self.deepseek_model,
            },
        }
        return provider_configs.get(self.ai_provider, {})
    
    def get_embedding_provider(self) -> str:
        """
        获取实际使用的 embedding 提供商
        如果配置为 auto，则根据 ai_provider 自动选择
        """
        if self.embedding_provider == "auto":
            # 根据对话模型选择 embedding 提供商
            # OpenAI 和 DeepSeek 使用 OpenAI 兼容的 embedding API
            # 其他使用豆包
            if self.ai_provider in ["openai", "deepseek"]:
                return "openai"
            elif self.ai_provider == "doubao":
                return "doubao"
            else:
                # Gemini, Claude 等没有独立的 embedding API，使用豆包
                # 如果没有配置豆包 key，回退到 OpenAI
                if self.doubao_api_key:
                    return "doubao"
                elif self.openai_api_key:
                    return "openai"
                else:
                    return "doubao"  # 默认
        return self.embedding_provider
    
    def get_embedding_config(self) -> dict:
        """获取 embedding 配置"""
        provider = self.get_embedding_provider()
        
        if provider == "openai":
            # OpenAI 兼容的 embedding (包括 DeepSeek)
            if self.ai_provider == "deepseek":
                return {
                    "api_key": self.deepseek_api_key,
                    "base_url": self.deepseek_base_url,
                    "model": "text-embedding-ada-002",  # DeepSeek 可能不支持，会回退
                    "dimension": self.openai_embedding_dimension,
                }
            else:
                return {
                    "api_key": self.openai_api_key,
                    "base_url": self.openai_base_url,
                    "model": self.openai_embedding_model,
                    "dimension": self.openai_embedding_dimension,
                }
        else:
            # 豆包
            return {
                "api_key": self.doubao_api_key,
                "base_url": self.doubao_base_url,
                "model": self.doubao_embedding_model,
                "dimension": self.doubao_embedding_dimension,
            }


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


# 导出配置实例
settings = get_settings()
