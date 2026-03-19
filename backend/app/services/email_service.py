"""
邮件服务
处理邮件发送相关功能
"""
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.config import get_settings


async def send_verification_code(email: str, code: str, expire_minutes: int = 5) -> bool:
    """
    发送验证码邮件
    
    Args:
        email: 收件人邮箱
        code: 验证码
        expire_minutes: 验证码过期时间（分钟）
    
    Returns:
        发送成功返回 True，否则返回 False
    """
    settings = get_settings()
    
    # 创建邮件内容
    subject = "【智教云】邮箱验证码"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
                background-color: #f5f5f5;
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
                font-weight: 500;
            }}
            .content {{
                padding: 40px 30px;
            }}
            .greeting {{
                font-size: 16px;
                color: #333;
                margin-bottom: 20px;
            }}
            .code-box {{
                background-color: #f8f9fa;
                border: 2px dashed #667eea;
                border-radius: 8px;
                padding: 20px;
                text-align: center;
                margin: 20px 0;
            }}
            .verification-code {{
                font-size: 32px;
                font-weight: bold;
                color: #667eea;
                letter-spacing: 8px;
                font-family: 'Courier New', monospace;
            }}
            .expire-notice {{
                font-size: 14px;
                color: #666;
                margin-top: 20px;
                padding: 15px;
                background-color: #fff3cd;
                border-radius: 4px;
                border-left: 4px solid #ffc107;
            }}
            .footer {{
                padding: 20px 30px;
                background-color: #f8f9fa;
                text-align: center;
                font-size: 12px;
                color: #999;
            }}
            .warning {{
                font-size: 12px;
                color: #999;
                margin-top: 20px;
                padding-top: 20px;
                border-top: 1px solid #eee;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>智教云</h1>
            </div>
            <div class="content">
                <p class="greeting">您好！</p>
                <p>您正在进行邮箱验证操作，请输入以下验证码完成验证：</p>
                
                <div class="code-box">
                    <div class="verification-code">{code}</div>
                </div>
                
                <div class="expire-notice">
                    ⏰ 验证码将在 <strong>{expire_minutes} 分钟</strong> 后过期，请及时使用。
                </div>
                
                <div class="warning">
                    <p>如果您没有请求此验证码，请忽略此邮件。请勿将验证码透露给他人。</p>
                </div>
            </div>
            <div class="footer">
                <p>此邮件由系统自动发送，请勿回复。</p>
                <p>© 智教云 - 让教育更智能</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # 创建邮件消息
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    message["To"] = email
    
    # 添加 HTML 内容
    html_part = MIMEText(html_content, "html", "utf-8")
    message.attach(html_part)
    
    try:
        # 调试信息
        print(f"正在连接 SMTP 服务器: {settings.SMTP_HOST}:{settings.SMTP_PORT}")
        print(f"使用用户名: {settings.SMTP_USER}")
        
        # 连接到 SMTP 服务器并发送邮件
        if settings.SMTP_USE_TLS:
            # 使用 SSL 连接（端口 465）
            print("使用 SSL/TLS 连接...")
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                use_tls=True
            )
        else:
            # 使用 STARTTLS（端口 587）
            print("使用 STARTTLS 连接...")
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                start_tls=True,
                tls_context=None  # 使用默认 TLS 上下文
            )
        print(f"邮件发送成功: {email}")
        return True
    except Exception as e:
        print(f"邮件发送失败: {e}")
        import traceback
        traceback.print_exc()
        return False
