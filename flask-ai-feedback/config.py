import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

class Config:
    """集中管理应用的配置"""
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 新增：设置数据库连接池回收时间（秒）
    # 这将防止因数据库连接超时而导致的 "server closed connection" 错误
    SQLALCHEMY_POOL_RECYCLE = 280
    
    # Google OAuth 配置
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
    
    # 授权用户邮箱列表
    AUTHORIZED_EMAILS = [email.strip() for email in os.getenv('AUTHORIZED_EMAILS', '').split(',')]
    
    # 第三方服务 API Keys
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

