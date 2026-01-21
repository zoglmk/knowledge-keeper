"""
设置 API - 管理应用配置
"""

from fastapi import APIRouter
from pydantic import BaseModel
from pathlib import Path
from typing import Optional
import os
import re

router = APIRouter(prefix="/config", tags=["config"])

# API Key 的映射关系
PROVIDER_KEY_MAP = {
    "doubao": "DOUBAO_API_KEY",
    "openai": "OPENAI_API_KEY",
    "claude": "CLAUDE_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
}


class ConfigUpdate(BaseModel):
    """配置更新请求"""
    provider: str
    api_key: str


class ConfigResponse(BaseModel):
    """配置响应"""
    provider: str
    has_api_key: bool  # 不返回实际密钥，只标记是否已配置
    message: str


def get_env_path() -> Path:
    """获取 .env 文件路径"""
    return Path(__file__).parent.parent.parent / ".env"


def read_env_file() -> dict:
    """读取 .env 文件"""
    env_path = get_env_path()
    config = {}
    
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    
    return config


def update_env_file(key: str, value: str) -> bool:
    """更新 .env 文件中的配置项"""
    env_path = get_env_path()
    
    if not env_path.exists():
        return False
    
    # 读取文件内容
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 查找并更新
    updated = False
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(f"{key}="):
            new_lines.append(f"{key}={value}\n")
            updated = True
        else:
            new_lines.append(line)
    
    # 如果没找到，添加新行
    if not updated:
        new_lines.append(f"\n{key}={value}\n")
    
    # 写回文件
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    return True


@router.get("", response_model=ConfigResponse)
async def get_config():
    """
    获取当前配置
    """
    config = read_env_file()
    provider = config.get("AI_PROVIDER", "doubao")
    
    # 检查当前提供商是否有 API Key
    key_name = PROVIDER_KEY_MAP.get(provider, "DOUBAO_API_KEY")
    api_key = config.get(key_name, "")
    has_key = bool(api_key and api_key != f"your-{provider}-api-key")
    
    return ConfigResponse(
        provider=provider,
        has_api_key=has_key,
        message="配置加载成功"
    )


@router.post("", response_model=ConfigResponse)
async def update_config(data: ConfigUpdate):
    """
    更新配置
    
    注意：更新后需要重启后端服务才能生效
    """
    provider = data.provider
    api_key = data.api_key
    
    # 验证提供商
    if provider not in PROVIDER_KEY_MAP:
        return ConfigResponse(
            provider=provider,
            has_api_key=False,
            message=f"不支持的提供商: {provider}"
        )
    
    # 更新 AI_PROVIDER
    update_env_file("AI_PROVIDER", provider)
    
    # 更新对应的 API Key
    key_name = PROVIDER_KEY_MAP[provider]
    update_env_file(key_name, api_key)
    
    return ConfigResponse(
        provider=provider,
        has_api_key=bool(api_key),
        message="配置已保存！请重启后端服务使配置生效。"
    )
