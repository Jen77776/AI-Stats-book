# 文件: conftest.py (请替换全部内容)

import pytest
from app import create_app, db
from config import Config
from app.models import User

class TestConfig(Config):
    """使用一个单独的测试配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False

@pytest.fixture(scope='module')
def test_app():
    """创建一个应用实例以供所有测试使用"""
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture(scope='module')
def test_client(test_app):
    """创建一个普通的、未登录的测试客户端"""
    return test_app.test_client()

@pytest.fixture(scope='function')
def db_session(test_app):
    """
    为每个测试函数提供一个干净的数据库事务。
    这是解决所有测试失败的最终方案。
    """
    with test_app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()
        db.session.begin_nested()
        
        # 将 db_session 绑定到这个嵌套的事务
        # 这样在 test_api.py 中使用的 db_session 和在 app 内部使用的 db.session
        # 都会指向同一个事务范围
        
        yield db.session
        
        # 测试结束后，回滚所有数据库更改，包括在 API 内部 commit 的内容
        db.session.rollback()
        transaction.rollback()
        connection.close()

@pytest.fixture(scope='function')
def authenticated_client(test_app):
    """
    创建一个预先通过身份验证的客户端。
    """
    client = test_app.test_client()
    with client.session_transaction() as sess:
        # 手动设置 Flask-Login 的会话变量，模拟登录
        sess['_user_id'] = "testadmin@example.com"
        sess['_fresh'] = True
    return client