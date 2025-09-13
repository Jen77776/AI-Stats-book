# 业务逻辑: 封装所有核心功能 (调用AI, 上传图片等)import os
import re
import json
import gspread
import google.generativeai as genai
from oauth2client.service_account import ServiceAccountCredentials
from .models import Question

# 初始化 Gemini 模型
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    model = None
    print(f"Failed to initialize Gemini model: {e}")

# --- AI/Gemini 服务 ---

def clean_json_from_ai_response(ai_text):
    """从可能包含 markdown 格式的字符串中提取 JSON 对象"""
    match = re.search(r'```(json)?\s*({.*?})\s*```', ai_text, re.DOTALL)
    if match:
        return match.group(2)
    return ai_text.strip()

def is_answer_ai_generated(student_answer):
    """使用 AI 判断答案是否由 AI 生成"""
    if not model:
        return False  # 安全失败

    try:
        prompt = f"""
        You are an expert text classifier. Your task is to determine if the following student's response was likely written by an AI or a human.
        You must respond with only a valid JSON object containing a single key: "classification".
        The value for "classification" must be one of two strings: "AI" or "Human".

        Example Response:
        {{
          "classification": "AI"
        }}

        Now, analyze the following text:
        ---
        Student's text: "{student_answer}"
        ---
        """
        response = model.generate_content(prompt)
        cleaned_text = clean_json_from_ai_response(response.text)
        result_json = json.loads(cleaned_text)
        classification = result_json.get("classification", "").lower()
        return classification == "ai"
    except Exception as e:
        print(f"AI detection error or invalid JSON response: {e}")
        return False

def get_feedback_and_grade(prompt_id, student_answer):
    """从 AI 获取反馈和评分"""
    if not model:
        return "AI model failed to load.", "N/A"

    question = Question.query.filter_by(prompt_id=prompt_id).first()
    if not question:
        return "Error: The requested prompt (question) could not be found.", "Error"

    system_prompt = question.ai_prompt
    try:
        full_prompt = f"""
        {system_prompt}
        ---
        TASK:
        Based on the rubric and guidelines above, analyze the following student's answer.
        You MUST respond with only a valid JSON object containing two keys:
        1.  "grade": A string classifying the student's performance...
        2.  "feedback": A string containing the helpful, warm, and encouraging feedback...

        Student's answer: "{student_answer}"
        """
        response = model.generate_content(full_prompt)
        cleaned_text = clean_json_from_ai_response(response.text)
        result_json = json.loads(cleaned_text)
        grade = result_json.get("grade", "N/A")
        feedback = result_json.get("feedback", "Could not generate feedback.")
        return feedback, grade
    except Exception as e:
        print(f"Error getting feedback and grade: {e}")
        return "Sorry, an error occurred while getting feedback.", "Error"

def get_summary_from_ai(all_answers_text):
    """为一组答案生成 AI 摘要"""
    if not model:
        return "AI model failed to load."

    summary_prompt = f"""
        You are an expert teaching assistant...
        Here are the student answers to analyze:
        ---
        {all_answers_text}
        ---
        """
    try:
        summary_response = model.generate_content(summary_prompt)
        return summary_response.text
    except Exception as e:
        print(f"Summary generation error: {e}")
        return f"Error generating summary: {e}"

