# 数据模型: 定义所有数据库表 (User, Question, Response)
from datetime import datetime
from flask_login import UserMixin
from . import db  # 从 app 包的 __init__.py 导入 db 实例

class User(UserMixin):
    """用户模型，用于 Flask-Login"""
    def __init__(self, user_id):
        self.id = user_id

class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    prompt_id = db.Column(db.String(100), unique=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    ai_prompt = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Response(db.Model):
    __tablename__ = 'responses'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(100))
    question = db.Column(db.Text, nullable=False)
    student_answer = db.Column(db.Text, nullable=False)
    ai_feedback = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    rating = db.Column(db.Integer)
    feedback_comment = db.Column(db.Text)
    is_ai_generated = db.Column(db.Boolean, default=False, nullable=False)
    performance_grade = db.Column(db.String(50))
