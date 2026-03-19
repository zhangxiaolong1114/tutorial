#!/usr/bin/env python3
"""
邮件发送测试脚本
"""
import asyncio
import sys
sys.path.insert(0, '/home/iecube_xiaolong/project/tutorial/backend')

from app.services.email_service import send_verification_code

async def test_email():
    """测试邮件发送"""
    test_email = input("请输入测试邮箱地址: ")
    test_code = "123456"
    
    print(f"\n正在发送测试邮件到 {test_email}...")
    print(f"验证码: {test_code}")
    
    success = await send_verification_code(test_email, test_code)
    
    if success:
        print("✅ 邮件发送成功！")
    else:
        print("❌ 邮件发送失败！")

if __name__ == "__main__":
    asyncio.run(test_email())
