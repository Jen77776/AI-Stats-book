import json
from app.models import Question, Response

# --- 公共和学生端 API 测试 ---

def test_evaluate_api(test_client, db_session, monkeypatch):
    """测试: POST /api/evaluate 端点应能成功创建一条反馈记录。"""
    # 准备
    prompt_id = "api-test-prompt"
    db_session.add(Question(prompt_id=prompt_id, title="API Test", question_text="Q", ai_prompt="A"))
    db_session.commit()

    monkeypatch.setattr('app.services.is_answer_ai_generated', lambda x: False)
    monkeypatch.setattr('app.services.get_feedback_and_grade', lambda x, y: ("Mock Feedback", "Mock Grade"))

    # 行为
    response = test_client.post('/api/evaluate', json={
        'answer': 'student answer', 'prompt_id': prompt_id, 'student_id': 'student123'
    })
    
    # 断言
    assert response.status_code == 200
    assert Response.query.count() == 1
    assert Response.query.first().student_id == 'student123'

def test_rate_feedback_api(test_client, db_session):
    """测试: POST /api/rate-feedback 端点应能成功更新一条反馈记录。"""
    # 准备
    response_rec = Response(question="q1", student_answer="a1", ai_feedback="f1")
    db_session.add(response_rec)
    db_session.commit()
    
    # 行为
    response = test_client.post('/api/rate-feedback', json={
        'response_id': response_rec.id, 'rating': 5, 'comment': 'Helpful'
    })

    # 断言
    assert response.status_code == 200
    updated_rec = Response.query.get(response_rec.id)
    assert updated_rec.rating == 5
    assert updated_rec.feedback_comment == 'Helpful'

def test_get_question_details_api(test_client, db_session):
    """测试: GET /api/question-details/<id> 端点应能返回正确的问题详情。"""
    # 准备
    prompt_id = "details-test"
    db_session.add(Question(prompt_id=prompt_id, title="Details Test", question_text="Details Q", ai_prompt="A"))
    db_session.commit()

    # 行为
    response = test_client.get(f'/api/question-details/{prompt_id}')

    # 断言
    assert response.status_code == 200
    data = response.get_json()
    assert data['title'] == "Details Test"
    assert data['question_text'] == "Details Q"

# --- 管理员端 API 测试 (需要认证) ---

def test_get_all_feedback_as_admin(authenticated_client, db_session):
    """测试: 已登录的管理员应能获取所有反馈。"""
    # 准备
    db_session.add(Response(question="q1", student_answer="a1", ai_feedback="f1"))
    db_session.add(Response(question="q2", student_answer="a2", ai_feedback="f2"))
    db_session.commit()

    # 行为
    response = authenticated_client.get('/api/get-all-feedback')

    # 断言
    assert response.status_code == 200
    assert len(response.get_json()) == 2

def test_create_question_as_admin(authenticated_client, monkeypatch):
    """测试: 已登录的管理员应能创建新问题。"""
    # 准备: 模拟 Cloudinary 上传
    monkeypatch.setattr('cloudinary.uploader.upload', lambda x: {'secure_url': 'http://mock.url/image.png'})

    # 行为
    response = authenticated_client.post('/api/create-question', data={
        'title': 'New Test Question', 'question_text': 'Q', 'ai_prompt': 'A'
    })
    
    # 断言
    assert response.status_code == 200
    assert Question.query.count() == 1
    assert Question.query.first().title == 'New Test Question'

def test_clear_problem_feedback_as_admin(authenticated_client, db_session):
    """测试: 已登录的管理员应能清除单个问题的反馈。"""
    # 准备
    db_session.add(Response(question="problem-to-clear", student_answer="a1", ai_feedback="f1"))
    db_session.add(Response(question="another-problem", student_answer="a2", ai_feedback="f2"))
    db_session.commit()
    assert Response.query.count() == 2

    # 行为
    response = authenticated_client.post('/api/clear-problem-feedback', json={'prompt_id': 'problem-to-clear'})
    
    # 断言
    assert response.status_code == 200
    assert Response.query.count() == 1
    assert Response.query.first().question == 'another-problem'

def test_clear_all_feedback_as_admin(authenticated_client, db_session):
    """测试: 已登录的管理员应能清除所有反馈。"""
    # 准备
    db_session.add(Response(question="q1", student_answer="a1", ai_feedback="f1"))
    db_session.commit()
    assert Response.query.count() == 1

    # 行为
    response = authenticated_client.post('/api/clear-all-feedback')
    
    # 断言
    assert response.status_code == 200
    assert Response.query.count() == 0

def test_get_summary_with_filter_as_admin(authenticated_client, db_session, monkeypatch):
    """新增测试: 当带有 prompt_id 参数时，应只总结特定问题的反馈。"""
    # 准备
    db_session.add(Response(question="q1", student_answer="Answer for Q1.", ai_feedback="f1"))
    db_session.add(Response(question="q2", student_answer="Answer for Q2.", ai_feedback="f2"))
    db_session.commit()
    def mock_summary_filtered(text):
        assert "Answer for Q1." not in text # 验证不包含其他问题的答案
        assert "Answer for Q2." in text
        return "Mock AI Summary for Q2"
    monkeypatch.setattr('app.services.get_summary_from_ai', mock_summary_filtered)

    # 行为
    response = authenticated_client.get('/api/get-summary?prompt_id=q2')

    # 断言
    assert response.status_code == 200
    assert response.get_json()['summary'] == "Mock AI Summary for Q2"
def test_rate_feedback_nonexistent_id(test_client):
    """新增测试: 当传入不存在的 response_id 时，API 应返回 404。"""
    # 行为
    response = test_client.post('/api/rate-feedback', json={
        'response_id': 99999, 'rating': 5, 'comment': 'Helpful'
    })
    # 断言
    assert response.status_code == 404