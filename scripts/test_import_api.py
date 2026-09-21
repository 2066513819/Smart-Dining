"""
测试供应商价格导入 API
用于验证后端 API 是否正常工作
"""

import requests
import sys
from pathlib import Path

# 测试配置
BASE_URL = "http://localhost:8000"  # 修改为您的后端地址
LOGIN_URL = f"{BASE_URL}/auth/token"
PREVIEW_URL = f"{BASE_URL}/supplier-price-import/preview-supplier-prices"
IMPORT_URL = f"{BASE_URL}/supplier-price-import/import-supplier-prices"

# 测试文件路径（请修改为您的测试文件）
TEST_FILE = Path(__file__).parent.parent / "26年1月商品入库价格表.xlsx"

def test_api():
    """测试 API 是否正常工作"""
    
    print("=" * 80)
    print("供应商价格导入 API 测试")
    print("=" * 80)
    
    # 1. 检查 API 文档是否可以访问
    print("\n1. 检查 API 文档...")
    try:
        resp = requests.get(f"{BASE_URL}/docs", timeout=5)
        if resp.status_code == 200:
            print("   ✓ API 文档可访问")
        else:
            print(f"   ✗ API 文档返回状态码: {resp.status_code}")
    except Exception as e:
        print(f"   ✗ 无法连接到后端: {e}")
        return
    
    # 2. 检查导入接口是否在 API 文档中
    print("\n2. 检查 OpenAPI 规范...")
    try:
        resp = requests.get(f"{BASE_URL}/openapi.json", timeout=5)
        if resp.status_code == 200:
            api_spec = resp.json()
            paths = api_spec.get('paths', {})
            
            import_path = "/supplier-price-import/import-supplier-prices"
            preview_path = "/supplier-price-import/preview-supplier-prices"
            
            if import_path in paths:
                print(f"   ✓ 导入接口已注册: {import_path}")
            else:
                print(f"   ✗ 导入接口未找到: {import_path}")
                print(f"   可用路径: {list(paths.keys())[:10]}...")  # 显示前10个路径
            
            if preview_path in paths:
                print(f"   ✓ 预览接口已注册: {preview_path}")
            else:
                print(f"   ✗ 预览接口未找到: {preview_path}")
    except Exception as e:
        print(f"   ✗ 获取 API 规范失败: {e}")
    
    # 3. 尝试直接调用预览接口（不带认证，应该返回 401）
    print("\n3. 测试预览接口（无认证）...")
    try:
        if TEST_FILE.exists():
            with open(TEST_FILE, 'rb') as f:
                resp = requests.post(PREVIEW_URL, files={'file': f}, timeout=10)
            
            if resp.status_code == 401:
                print("   ✓ 接口存在，需要认证（这是正常的）")
            elif resp.status_code == 404:
                print(f"   ✗ 接口不存在 (404): {PREVIEW_URL}")
                print("   请确保后端服务已重启，并且新代码已加载")
            else:
                print(f"   ? 返回状态码: {resp.status_code}")
                print(f"   响应: {resp.text[:200]}")
        else:
            print(f"   ! 测试文件不存在: {TEST_FILE}")
    except Exception as e:
        print(f"   ✗ 请求失败: {e}")
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)
    print("\n建议:")
    print("1. 如果看到 '接口不存在 (404)'，请重启后端服务:")
    print("   uvicorn app.main:app --reload")
    print("2. 确认代码已保存到:")
    print("   - app/routers/supplier_price_import.py")
    print("   - app/main.py")
    print("3. 刷新浏览器页面，清除缓存 (Ctrl+F5)")

if __name__ == "__main__":
    test_api()
