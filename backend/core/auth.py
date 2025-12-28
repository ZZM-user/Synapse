# backend/core/auth.py
"""
API 认证模块

提供轻量级的 Bearer Token 认证机制，保护管理后台 API。
MCP 协议端点不受此认证影响，将来会有独立的认证机制。
"""
import os
from typing import Optional

from fastapi import Security, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# HTTP Bearer Token 安全方案
security = HTTPBearer(auto_error=False)


def get_api_token() -> Optional[str]:
    """
    从环境变量获取 API Token

    Returns:
        配置的 API Token，如果未配置则返回 None
    """
    return os.getenv("SYNAPSE_API_TOKEN")


async def verify_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> str:
    """
    验证 API Token

    Args:
        credentials: HTTP Bearer 认证凭据

    Returns:
        验证通过的 token

    Raises:
        HTTPException: Token 无效或缺失时抛出 401 错误

    工作模式：
    - 如果未配置 SYNAPSE_API_TOKEN 环境变量，则跳过鉴权（开发模式）
    - 如果配置了，则要求请求必须携带正确的 token
    """
    api_token = get_api_token()

    # 开发模式：未配置 token，跳过鉴权
    if not api_token:
        print("⚠️  警告: 未配置 SYNAPSE_API_TOKEN，API 鉴权已禁用（仅用于开发）")
        return "dev-mode"

    # 生产模式：必须提供有效 token
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if credentials.credentials != api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return credentials.credentials


# 导出为依赖项
RequireAuth = Security(verify_token)
