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
    # 豆包多模态 embedding 模型
    doubao_embedding_model: str = "doubao-embedding-vision-250615"
    embedding_dimension: int = 3072  # doubao-embedding-vision 维度
    
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


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


# 导出配置实例
settings = get_settings()
