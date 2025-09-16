import json
from unittest.mock import MagicMock
import pytest
from app import services
from app.models import Question


def test_is_answer_ai_generated(monkeypatch):
    """
    测试: is_answer_ai_generated 函数应能正确解析模拟的 AI 响应。
    """
    # 1. 准备：模拟 AI 响应对象
    mock_response = MagicMock()

    # Case 1: AI 生成的回答（返回 "AI"）
    mock_response.text = '{"classification": "AI"}'
    mock_generate_content = MagicMock(return_value=mock_response)
    monkeypatch.setattr(services.model, "generate_content", mock_generate_content)

    assert services.is_answer_ai_generated("some answer") is True

    # Case 2: 人类书写（返回 "Human"）
    mock_response.text = '{"classification": "Human"}'
    # 无需重新设置 mock_generate_content，因为 monkeypatch 已绑定
    # 但为了清晰，可以再次赋值
    mock_generate_content.return_value = mock_response

    assert services.is_answer_ai_generated("some answer") is False

    # Case 3: 非法 JSON 响应（应安全返回 False）
    mock_response.text = "This is not JSON!"
    mock_generate_content.return_value = mock_response

    assert services.is_answer_ai_generated("some answer") is False


def test_get_feedback_and_grade(monkeypatch, db_session):
    """
    测试: get_feedback_and_grade 函数应能从数据库获取问题，
    并正确解析模拟的 AI 响应以返回反馈和评分。
    """
    # 1. 准备：在测试数据库中创建一个虚拟问题
    dummy_question = Question(
        prompt_id="test-prompt-1",
        title="Test Question",
        question_text="What is 2+2?",
        ai_prompt="Please evaluate the answer."
    )
    db_session.add(dummy_question)
    db_session.commit()

    # 2. 准备：模拟 AI 响应（带 Markdown 包裹的 JSON）
    mock_response = MagicMock()
    expected_feedback = "Great job!"
    expected_grade = "Excellent"

    # 方法一：直接返回 JSON 字符串（推荐，最稳定）
    mock_response.text = f'{{"feedback": "{expected_feedback}", "grade": "{expected_grade}"}}'

    # 方法二：如果需要测试 markdown 包裹版本，取消注释以下行（可选）
    # mock_response.text = f'```json\n{{"feedback": "{expected_feedback}", "grade": "{expected_grade}"}}\n```'

    # 3. 行为：替换真实的 API 调用
    mock_generate_content = MagicMock(return_value=mock_response)
    monkeypatch.setattr(services.model, "generate_content", mock_generate_content)

    # 4. 断言：调用函数并验证返回值是否符合预期
    feedback, grade = services.get_feedback_and_grade("test-prompt-1", "The answer is 4.")

    assert feedback == expected_feedback
    assert grade == expected_grade