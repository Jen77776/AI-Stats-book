import re
from datetime import datetime
import cloudinary.uploader
from flask import Blueprint, request, jsonify
from flask_login import login_required
from .. import db
from ..models import Question, Response
from .. import services  # 导入我们的服务模块
import google.generativeai as genai

# 创建一个名为 'api' 的蓝图
api_bp = Blueprint('api', __name__)

# --- 学生/Tutor API ---

@api_bp.route('/evaluate', methods=['POST'])
def handle_evaluation():
    data = request.get_json()
    student_answer = data.get('answer')
    student_id = data.get('student_id', 'anonymous')
    prompt_id = data.get('prompt_id')

    if not prompt_id:
        return jsonify({'error': 'A prompt_id must be provided.'}), 400
    
    is_ai = services.is_answer_ai_generated(student_answer)
    ai_feedback, performance_grade = services.get_feedback_and_grade(prompt_id, student_answer)

    new_response = Response(
        student_id=student_id,
        question=prompt_id,
        student_answer=student_answer,
        ai_feedback=ai_feedback,
        is_ai_generated=is_ai,
        performance_grade=performance_grade
    )
    db.session.add(new_response)
    db.session.commit()
    return jsonify({'feedback': ai_feedback, 'response_id': new_response.id})

@api_bp.route('/rate-feedback', methods=['POST'])
def rate_feedback():
    data = request.get_json()
    response_id = data.get('response_id')
    rating = data.get('rating')
    comment = data.get('comment', '')

    response_to_update = Response.query.get(response_id)
    if response_to_update:
        response_to_update.rating = rating
        response_to_update.feedback_comment = comment
        db.session.commit()
        return jsonify({'status': 'success'}), 200
    return jsonify({'status': 'error', 'message': 'Response not found'}), 404

@api_bp.route('/question-details/<string:prompt_id>')
def get_question_details(prompt_id):
    question = Question.query.filter_by(prompt_id=prompt_id).first()
    if question:
        return jsonify({
            'title': question.title,
            'question_text': question.question_text,
            'image_src': question.image_url
        })
    return jsonify({'error': 'Question details not found'}), 404

# --- Admin Panel API ---

@api_bp.route('/get-unique-problems', methods=['GET'])
@login_required
def get_unique_problems():
    """为仪表盘的筛选菜单提供所有问题的列表"""
    try:
        all_questions = Question.query.order_by(Question.created_at.desc()).all()
        problem_list = [{
            'prompt_id': q.prompt_id,
            'title': q.title
        } for q in all_questions]
        return jsonify(problem_list)
    except Exception as e:
        print(f"Error getting unique problems from DB: {e}")
        return jsonify([]), 500

@api_bp.route('/get-all-feedback', methods=['GET'])
@login_required
def get_all_feedback():
    prompt_id_filter = request.args.get('prompt_id')
    query = Response.query
    if prompt_id_filter:
        query = query.filter(Response.question == prompt_id_filter)
    
    responses = query.order_by(Response.timestamp.desc()).all()
    output = [{
        'id': r.id, 'student_id': r.student_id, 'question': r.question,
        'student_answer': r.student_answer, 'ai_feedback': r.ai_feedback,
        'timestamp': r.timestamp.isoformat(), 'rating': r.rating,
        'feedback_comment': r.feedback_comment, 'is_ai_generated': r.is_ai_generated,
        'performance_grade': r.performance_grade
    } for r in responses]
    return jsonify(output)

@api_bp.route('/get-summary', methods=['GET'])
@login_required
def get_summary():
    prompt_id_filter = request.args.get('prompt_id')
    query = Response.query.filter(Response.is_ai_generated == False)
    if prompt_id_filter and prompt_id_filter != 'all':
        query = query.filter(Response.question == prompt_id_filter)
    
    responses = query.all()
    if not responses:
        return jsonify({'summary': 'Not enough data to generate a summary.'})

    all_answers_text = "\n\n---\n\n".join([res.student_answer for res in responses])
    summary = services.get_summary_from_ai(all_answers_text)
    return jsonify({'summary': summary})

@api_bp.route('/clear-problem-feedback', methods=['POST'])
@login_required
def clear_problem_feedback():
    data = request.get_json()
    prompt_id = data.get('prompt_id')
    if not prompt_id:
        return jsonify({'status': 'error', 'message': 'A prompt_id must be provided.'}), 400

    try:
        Response.query.filter_by(question=prompt_id).delete()
        db.session.commit()
        return jsonify({'status': 'success', 'message': f'Data for {prompt_id} cleared.'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
@api_bp.route('/clear-all-feedback', methods=['POST'])
@login_required
def clear_all_feedback():
    """Deletes all records from the 'responses' table."""
    try:
        db.session.query(Response).delete()
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'All feedback data has been cleared.'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error clearing all data: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
@api_bp.route('/create-question', methods=['POST'])
@login_required
def create_question():
    title = request.form.get('title')
    question_text = request.form.get('question_text')
    ai_prompt = request.form.get('ai_prompt')
    image_file = request.files.get('image')

    if not title or not question_text or not ai_prompt:
        return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400

    image_url = None
    if image_file:
        try:
            upload_result = cloudinary.uploader.upload(image_file)
            image_url = upload_result.get('secure_url')
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'Image upload failed: {e}'}), 500

    base_id = re.sub(r'[^a-z0-9-]+', '', title.lower().replace(' ', '-'))
    prompt_id = f"{base_id}-{int(datetime.now().timestamp())}"

    new_question = Question(
        prompt_id=prompt_id, title=title, question_text=question_text,
        ai_prompt=ai_prompt, image_url=image_url
    )
    db.session.add(new_question)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': 'Question created successfully!',
        'prompt_id': prompt_id
    })
@api_bp.route('/get-all-questions', methods=['GET'])
@login_required
def get_all_questions():
    """为编辑页面提供所有问题的完整数据"""
    try:
        all_questions = Question.query.order_by(Question.created_at.desc()).all()
        questions_list = [{
            'prompt_id': q.prompt_id,
            'title': q.title,
            'question_text': q.question_text,
            'ai_prompt': q.ai_prompt,
            'image_url': q.image_url
        } for q in all_questions]
        return jsonify(questions_list)
    except Exception as e:
        print(f"Error getting all questions from DB: {e}")
        return jsonify([]), 500
@api_bp.route('/update-question/<string:prompt_id>', methods=['POST'])
@login_required
def update_question(prompt_id):
    """根据 prompt_id 更新一个已存在的问题"""
    question = Question.query.filter_by(prompt_id=prompt_id).first()
    if not question:
        return jsonify({'status': 'error', 'message': 'Question not found'}), 404

    try:
        question.title = request.form.get('title', question.title)
        question.question_text = request.form.get('question_text', question.question_text)
        question.ai_prompt = request.form.get('ai_prompt', question.ai_prompt)
        
        image_file = request.files.get('image')
        if image_file:
            # 如果上传了新图片，则上传到 Cloudinary 并更新 URL
            upload_result = cloudinary.uploader.upload(image_file)
            question.image_url = upload_result.get('secure_url')

        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Question updated successfully!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'An error occurred: {e}'}), 500
@api_bp.route('/delete-question/<string:prompt_id>', methods=['DELETE'])
@login_required
def delete_question(prompt_id):
    """根据 prompt_id 删除一个问题及其所有相关的回答"""
    question = Question.query.filter_by(prompt_id=prompt_id).first()
    if not question:
        return jsonify({'status': 'error', 'message': 'Question not found'}), 404

    try:
        # 1. 删除所有与该问题相关的回答
        Response.query.filter_by(question=prompt_id).delete()
        
        # 2. 删除问题本身
        db.session.delete(question)
        
        # 3. 提交事务
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': 'Question and all associated responses have been deleted.'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting question {prompt_id}: {e}")
        return jsonify({'status': 'error', 'message': f'An error occurred: {e}'}), 500

@api_bp.route('/test-ai-connection', methods=['GET'])
def test_ai_connection():
    """
    一个专门用于测试后端服务器与 Google AI API 之间连接和认证的端点。
    它会尝试列出所有可用的模型。
    """
    try:
        # genai 库需要在应用启动时通过 API 密钥进行配置。
        # 我们假设这已经完成。
        # list_models() 是一个轻量级的调用，非常适合用来测试基础连接。
        models = list(genai.list_models())
        
        # 我们可以检查一下列表中是否包含我们需要的模型
        model_found = any('gemini-1.5-pro' in m.name for m in models)

        return jsonify({
            'status': 'success',
            'message': 'Successfully connected to Google AI API and listed models.',
            'total_models_found': len(models),
            'gemini_1.5_pro_is_available': model_found
        })
    except Exception as e:
        # 如果失败，返回从 Google API 库收到的确切错误信息，这对调试至关重要！
        return jsonify({
            'status': 'error',
            'message': 'Failed to connect or authenticate with Google AI API.',
            'error_details': str(e) # 将原始错误信息转换为字符串返回
        }), 500 # 返回 500 服务器内部错误状态码