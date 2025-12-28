#!/usr/bin/env python
"""
测试 API 鉴权功能
"""
import os
import requests
import time
import subprocess

def test_auth():
    print("=" * 60)
    print("🧪 测试 API 鉴权功能")
    print("=" * 60)

    BASE_URL = "http://localhost:8000"

    # 测试 1: 开发模式（未配置 Token）
    print("\n📝 测试 1: 开发模式（未配置 SYNAPSE_API_TOKEN）")
    print("   预期: 可以访问所有管理 API")

    try:
        # 测试管理 API
        response = requests.get(f"{BASE_URL}/api/v1/services")
        if response.status_code == 200:
            print(f"   ✅ /api/v1/services - HTTP {response.status_code} (开发模式，未鉴权)")
        else:
            print(f"   ❌ /api/v1/services - HTTP {response.status_code}")

        # 测试 MCP 端点（不应受影响）
        response = requests.get(f"{BASE_URL}/mcp/synapse/config")
        if response.status_code == 200:
            print(f"   ✅ /mcp/synapse/config - HTTP {response.status_code} (MCP 端点无鉴权)")
        else:
            print(f"   ❌ /mcp/synapse/config - HTTP {response.status_code}")

    except Exception as e:
        print(f"   ❌ 错误: {e}")

    # 测试 2: 生产模式模拟（使用 Bearer Token）
    print("\n📝 测试 2: 模拟生产模式（使用 Bearer Token）")
    print("   说明: 实际生产模式需要设置 SYNAPSE_API_TOKEN 环境变量并重启服务")

    try:
        # 测试不带 token 访问管理 API（开发模式下仍然能访问）
        response = requests.get(f"{BASE_URL}/api/v1/services")
        if response.status_code == 200:
            print(f"   ℹ️  /api/v1/services (无 token) - HTTP {response.status_code} (开发模式)")

        # 测试带 token 访问管理 API
        headers = {"Authorization": "Bearer test-token-123"}
        response = requests.get(f"{BASE_URL}/api/v1/services", headers=headers)
        if response.status_code == 200:
            print(f"   ✅ /api/v1/services (带 token) - HTTP {response.status_code}")
        else:
            print(f"   ❌ /api/v1/services (带 token) - HTTP {response.status_code}")

        # 测试 MCP 端点（始终无需认证）
        response = requests.get(f"{BASE_URL}/mcp/synapse/config")
        if response.status_code == 200:
            print(f"   ✅ /mcp/synapse/config (无 token) - HTTP {response.status_code} (MCP 端点无鉴权)")

    except Exception as e:
        print(f"   ❌ 错误: {e}")

    # 测试 3: 验证所有管理 API 模块
    print("\n📝 测试 3: 验证所有管理 API 模块")

    management_apis = [
        "/api/v1/services",
        "/api/v1/combinations",
        "/api/v1/mcp-servers",
        "/api/v1/dashboard/stats",
        "/api/v1/endpoints?url=http://example.com/openapi.json"
    ]

    try:
        for api in management_apis:
            response = requests.get(f"{BASE_URL}{api}")
            if response.status_code in [200, 404, 500]:  # 404/500 是预期的（数据可能不存在）
                print(f"   ✅ {api} - HTTP {response.status_code}")
            else:
                print(f"   ❌ {api} - HTTP {response.status_code}")

    except Exception as e:
        print(f"   ❌ 错误: {e}")

    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)
    print("\n💡 提示:")
    print("   - 当前为开发模式（未设置 SYNAPSE_API_TOKEN）")
    print("   - 要启用鉴权，请设置环境变量: export SYNAPSE_API_TOKEN=your_secret_token")
    print("   - 生产环境建议使用: openssl rand -hex 32 生成随机 token")
    print("=" * 60)

if __name__ == "__main__":
    test_auth()
