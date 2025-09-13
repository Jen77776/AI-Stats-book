import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_cors import CORS
from authlib.integrations.flask_client import OAuth
import cloudinary
import google.generativeai as genai

from config import Config

# 1. 初始化插件，但不传入 app 对象
db = SQLAlchemy()
login_manager = LoginManager()
oauth = OAuth()
cors = CORS()

# 声明 user_loader
@login_manager.user_loader
def load_user(user_id):
    # 局部导入以避免循环依赖
    from .models import User 
    return User(user_id)

def create_app(config_class=Config):
    """应用工厂函数"""
    # 创建 Flask app 实例
    # 将 template_folder 的路径指向项目根目录下的 templates 文件夹
    app = Flask(__name__, instance_relative_config=True, template_folder='../templates')
    
    # 从配置对象中加载配置
    app.config.from_object(config_class)

    # 2. 将 app 实例与插件绑定
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login' # 使用蓝图名称 'auth' 和路由 'login'
    oauth.init_app(app)
    cors.init_app(app)

    # --- 配置第三方服务 ---
    # 配置 Google OAuth
    oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        access_token_url='https://accounts.google.com/o/oauth2/token',
        access_token_params=None,
        authorize_url='https://accounts.google.com/o/oauth2/auth',
        authorize_params=None,
        api_base_url='https://www.googleapis.com/oauth2/v1/',
        userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
        client_kwargs={'scope': 'openid email profile'},
        jwks_uri="https://www.googleapis.com/oauth2/v3/certs",
    )

    # 配置 Cloudinary
    cloudinary.config(
        cloud_name=app.config["CLOUDINARY_CLOUD_NAME"],
        api_key=app.config["CLOUDINARY_API_KEY"],
        api_secret=app.config["CLOUDINARY_API_SECRET"]
    )
    
    # 配置 Gemini API
    try:
        genai.configure(api_key=app.config['GEMINI_API_KEY'])
    except Exception as e:
        print(f"Gemini API configuration failed: {e}")

    # --- 注册蓝图 ---
    from .blueprints.auth_views import auth_bp
    from .blueprints.api import api_bp
    
    app.register_blueprint(auth_bp)
    # 为所有 API 路由添加 /api 前缀
    app.register_blueprint(api_bp, url_prefix='/api')

    # 在应用上下文中创建数据库表
    with app.app_context():
        db.create_all()

    print(f"--- DATABASE URI IN USE: {app.config['SQLALCHEMY_DATABASE_URI']} ---")

    return app
