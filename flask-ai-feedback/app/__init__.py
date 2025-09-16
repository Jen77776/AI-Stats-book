import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_cors import CORS
from authlib.integrations.flask_client import OAuth
import cloudinary
import google.generativeai as genai
from flask_migrate import Migrate

from config import Config

# 初始化插件
db = SQLAlchemy()
login_manager = LoginManager()
oauth = OAuth()
cors = CORS()
migrate = Migrate()

@login_manager.user_loader
def load_user(user_id):
    from .models import User 
    return User(user_id)

def create_app(config_class=Config):
    """应用工厂函数"""
    app = Flask(__name__, instance_relative_config=True, template_folder='../templates')
    app.config.from_object(config_class)

    # 绑定插件
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    oauth.init_app(app)
    cors.init_app(app)

    # --- 配置第三方服务 ---
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

    # --- ↓↓↓ 这是修复的部分 ↓↓↓ ---
    # 确保使用关键字参数来调用 config 函数
    cloudinary.config(
        cloud_name=app.config["CLOUDINARY_CLOUD_NAME"],
        api_key=app.config["CLOUDINARY_API_KEY"],
        api_secret=app.config["CLOUDINARY_API_SECRET"]
    )
    
    try:
        genai.configure(api_key=app.config['GEMINI_API_KEY'])
    except Exception as e:
        print(f"Gemini API configuration failed: {e}")

    # --- 注册蓝图 ---
    from .blueprints.auth_views import auth_bp
    from .blueprints.api import api_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    print(f"--- DATABASE URI IN USE: {app.config['SQLALCHEMY_DATABASE_URI']} ---")

    return app

