#!/usr/bin/env python
"""
API 端点测试脚本
"""
import requests
import time

BASE_URL = "http://localhost:8000"

def test_api():
    print("=" * 60)
    print("🧪 开始测试 API 端点")
    print("=" * 60)

    # 等待服务器启动
    print("\n⏳ 等待服务器启动...")
    time.sleep(2)

    tests = [
        ("服务管理 API", f"{BASE_URL}/api/v1/services"),
        ("组合管理 API", f"{BASE_URL}/api/v1/combinations"),
        ("MCP 服务管理 API", f"{BASE_URL}/api/v1/mcp-servers"),
        ("Dashboard API", f"{BASE_URL}/api/v1/dashboard/stats"),
    ]

    passed = 0
    failed = 0

    for name, url in tests:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                count = len(data) if isinstance(data, list) else "N/A"
                print(f"✅ {name}: HTTP {response.status_code} (数据项: {count})")
                passed += 1
            else:
                print(f"❌ {name}: HTTP {response.status_code}")
                failed += 1
        except Exception as e:
            print(f"❌ {name}: {str(e)}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)

if __name__ == "__main__":
    test_api()
