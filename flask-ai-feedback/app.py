# app.py
import os
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import re 
from werkzeug.utils import secure_filename
import cloudinary
import cloudinary.uploader

load_dotenv()
app = Flask(__name__, instance_relative_config=True, template_folder='templates')
CORS(app)
cloudinary.config( 
  cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"), 
  api_key = os.getenv("CLOUDINARY_API_KEY"), 
  api_secret = os.getenv("CLOUDINARY_API_SECRET") 
)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
print(f"--- DATABASE URI IN USE: {app.config['SQLALCHEMY_DATABASE_URI']} ---")
class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    prompt_id = db.Column(db.String(100), unique=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    ai_prompt = db.Column(db.Text, nullable=False) # 替代 .txt 文件
    image_url = db.Column(db.String(255), nullable=True) # 替代 JSON 中的 image_src
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

with app.app_context():
    db.create_all()

# --- Key Information ---
# Warning: For security reasons, API keys should not be hard-coded.
# In a real deployment, use environment variables or a secure key management service.
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    print(f"API configuration failed: {e}")
    model = None

def get_generic_feedback(prompt_id, student_answer):
    if not model:
        return "AI model failed to load."
    
    try:
        # 根据prompt_id，从prompts文件夹读取对应的指令文件
        prompt_path = os.path.join('prompts', f'{prompt_id}.txt')
        with open(prompt_path, 'r', encoding='utf-8') as f:
            system_prompt = f.read()
        
        # 构建最终的Prompt并调用API
        full_prompt = f"{system_prompt}\n\nThe student's answer is:\n\"{student_answer}\""
        response = model.generate_content(full_prompt)
        return response.text
    except FileNotFoundError:
        print(f"Error: Prompt file not found at {prompt_path}")
        return "Error: The requested prompt (question) could not be found."
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return "Sorry, an error occurred while getting feedback from the AI."


def append_to_google_sheet(row_data):
    try:
        # define the scope for Google Sheets and Drive API
        scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/drive']

        # use service account credentials to authorize gspread
        creds = ServiceAccountCredentials.from_json_keyfile_name("google_credentials.json", scope)
        client = gspread.authorize(creds)

        sheet = client.open("AI Biostats Feedback").sheet1

        # add a new row with the provided data
        sheet.append_row(row_data)
        print("Successfully appended a row to Google Sheet.")
    except Exception as e:
        print(f"Google Sheet write error: {e}")

def update_gsheet_row(response_id, full_row_data):
    """Finds a row by its ID and updates it with new data."""
    try:
        scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name("google_credentials.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open("AI Biostats Feedback").sheet1

        # Find the cell that contains the unique response ID
        # Assumes the 'id' is in the first column of your Google Sheet
        cell = sheet.find(str(response_id), in_column=1)
        if cell:
            # gspread's update method takes a range and a list of lists.
            # Example: update('A5:H5', [[ ... values ... ]])
            start_col = gspread.utils.rowcol_to_a1(cell.row, 1)[0] # e.g., 'A'
            end_col = gspread.utils.rowcol_to_a1(cell.row, len(full_row_data))[0] # e.g., 'H'
            sheet.update(f'{start_col}{cell.row}:{end_col}{cell.row}', [full_row_data])
            print(f"Successfully updated row {cell.row} in Google Sheet.")
        else:
            print(f"Warning: Could not find response_id {response_id} in Google Sheet to update.")
    except Exception as e:
        print(f"Google Sheet update error: {e}")
def clean_json_from_ai_response(ai_text):
    """
    Extracts a JSON object from a string that might be wrapped in markdown.
    """
    match = re.search(r'```(json)?\s*({.*?})\s*```', ai_text, re.DOTALL)
    if match:
        return match.group(2)
    return ai_text.strip()
def is_answer_ai_generated(student_answer):
    """Uses AI to flag if an answer is likely AI-generated by asking for a JSON response."""
    if not model:
        return False # Fail safe
    
    try:
        # --- 这是新的、更可靠的Prompt ---
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

        # --- 这是新的、更可靠的解析逻辑 ---
        # 1. 尝试将AI的文本回复解析为JSON对象
        cleaned_text = clean_json_from_ai_response(response.text)
        result_json = json.loads(cleaned_text)
        # 2. 从JSON对象中获取分类结果
        classification = result_json.get("classification", "").lower()
        
        # 3. 检查分类结果并返回布尔值
        if classification == "ai":
            return True
        else:
            return False
            
    except Exception as e:
        # 如果AI没有返回有效的JSON，或者解析失败，都视为错误
        print(f"AI detection error or invalid JSON response: {e}")
        print(f"Original AI response text: {response.text}")
        return False # 如果检测失败，默认不是AI生成的
def get_feedback_and_grade(prompt_id, student_answer):
    """
    Gets both feedback and a performance grade from the AI using a structured JSON response.
    """
    if not model:
        return "AI model failed to load.", "N/A"

    # 从数据库获取问题和对应的AI指令
    question = Question.query.filter_by(prompt_id=prompt_id).first()
    if not question:
        return "Error: The requested prompt (question) could not be found.", "Error"

    system_prompt = question.ai_prompt # 从数据库字段获取 AI 指令

    try:
        # 新的、要求返回JSON的Prompt (这部分逻辑保持不变)
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
@app.route('/api/evaluate', methods=['POST'])
def handle_evaluation():
    data = request.get_json()
    student_answer = data.get('answer')
    student_id = data.get('student_id', 'anonymous')
    prompt_id = data.get('prompt_id')

    if not prompt_id:
        return jsonify({'error': 'A prompt_id must be provided.'}), 400
    
    is_ai = is_answer_ai_generated(student_answer)
    print(f"AI detection result for new answer: {is_ai}")
    
    # 调用新的评分函数，它会同时返回feedback和grade
    ai_feedback, performance_grade = get_feedback_and_grade(prompt_id, student_answer)

    new_response = Response(
        student_id=student_id,
        question=prompt_id,
        student_answer=student_answer,
        ai_feedback=ai_feedback,
        timestamp=datetime.now(),
        is_ai_generated=is_ai,
        performance_grade=performance_grade # <-- 将获取到的评级存入数据库
    )
    db.session.add(new_response)
    db.session.commit()
    return jsonify({'feedback': ai_feedback, 'response_id': new_response.id})
# --- Add the new endpoint for receiving ratings ---
@app.route('/api/rate-feedback', methods=['POST'])
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

        full_updated_row = [
            response_to_update.id, str(response_to_update.timestamp), response_to_update.student_id,
            response_to_update.question, response_to_update.student_answer, response_to_update.ai_feedback,
            response_to_update.rating, response_to_update.feedback_comment
        ]
        update_gsheet_row(response_id, [str(item) for item in full_updated_row])
        
        return jsonify({'status': 'success'}), 200
    
    return jsonify({'status': 'error', 'message': 'Response not found'}), 404

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/get-all-feedback', methods=['GET'])
def get_all_feedback():
    # 从URL的查询参数中获取 prompt_id
    prompt_id_filter = request.args.get('prompt_id')
    
    # 构建基础查询
    query = Response.query
    
    # 如果提供了 prompt_id，则添加筛选条件
    if prompt_id_filter:
        query = query.filter(Response.question == prompt_id_filter)
    
    # 按时间降序排序并获取所有结果
    responses = query.order_by(Response.timestamp.desc()).all()
    
    output = []
    for r in responses:
        output.append({
            'id': r.id,
            'student_id': r.student_id,
            'question': r.question, # 这个字段就是 prompt_id
            'student_answer': r.student_answer,
            'ai_feedback': r.ai_feedback,
            'timestamp': r.timestamp.isoformat(),
            'rating': r.rating,
            'feedback_comment': r.feedback_comment,
            'is_ai_generated': r.is_ai_generated,
            'performance_grade': r.performance_grade
        })
    return jsonify(output)
@app.route('/api/clear-problem-feedback', methods=['POST'])
def clear_problem_feedback():
    """
    Deletes all records for a specific problem (prompt_id).
    """
    data = request.get_json()
    prompt_id = data.get('prompt_id')

    if not prompt_id:
        return jsonify({'status': 'error', 'message': 'A prompt_id must be provided.'}), 400

    try:
        # --- 1. 从 PostgreSQL 数据库中删除特定问题的数据 ---
        responses_to_delete = Response.query.filter_by(question=prompt_id)
        num_deleted = responses_to_delete.delete()
        db.session.commit()
        print(f"Successfully deleted {num_deleted} responses for prompt_id '{prompt_id}' from the database.")

        # --- 2. 从 Google Sheet 中删除对应的行 (这部分比较复杂) ---
        try:
            scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/drive']
            creds = ServiceAccountCredentials.from_json_keyfile_name("google_credentials.json", scope)
            client = gspread.authorize(creds)
            sheet = client.open("AI Biostats Feedback").sheet1
            
            all_records = sheet.get_all_records() # 获取所有数据以便查找
            rows_to_delete_indices = []
            
            # 假设 'question' 列是第4列 (A=1, B=2, C=3, D=4)
            # gspread 的 get_all_records() 会使用 header 作为 key
            for i, record in enumerate(all_records):
                if record.get('question') == prompt_id:
                    # i 是从0开始的索引, 但 gspread 的行号从1开始, 且有表头
                    # 所以要删除的行号是 i + 2
                    rows_to_delete_indices.append(i + 2)

            # 为了避免删除时行号错乱，必须从后往前删除
            for row_index in sorted(rows_to_delete_indices, reverse=True):
                sheet.delete_rows(row_index)
            print(f"Successfully deleted rows for prompt_id '{prompt_id}' from Google Sheet.")

        except Exception as e:
            print(f"Google Sheet delete error: {e}")
            # 即使 GSheet 删除失败，我们仍然可以继续，因为数据库已经成功了
        
        return jsonify({'status': 'success', 'message': f'All data for problem {prompt_id} has been cleared.'}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error clearing data for problem {prompt_id}: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
@app.route('/api/get-summary', methods=['GET'])
def get_summary():
    """API endpoint to generate an AI-powered summary of all answers."""
    prompt_id_filter = request.args.get('prompt_id')
    query = Response.query.filter(Response.is_ai_generated == False)
    if prompt_id_filter and prompt_id_filter != 'all':
        query = query.filter(Response.question == prompt_id_filter)
    # 使用SQLAlchemy查询
    responses = query.all()
    if not responses:
        return jsonify({'summary': 'Not enough data to generate a summary.'})

    all_answers_text = "\n\n---\n\n".join([res.student_answer for res in responses])

    summary_prompt = f"""
        You are an expert teaching assistant analyzing student responses for a data visualization critique.
        Based on the following collection of student answers, please provide a concise, high-level summary for the instructor in markdown format.

        Address these key points:
        1.  **Overall Performance:** Briefly categorize the class's overall performance (e.g., Excellent, Good, Fair, Poor) and why.
        2.  **Common Points of Confusion:** List 2-3 topics or concepts that students commonly misunderstood or failed to mention.
        3.  **Creative/Insightful Answers:** Highlight one or two specific, creative, or insightful answers that stood out. Quote a small, impactful part of the answer.

        Here are the student answers to analyze:
        ---
        {all_answers_text}
        ---
        """
    try:
        summary_response = model.generate_content(summary_prompt)
        return jsonify({'summary': summary_response.text})
    except Exception as e:
        print(f"Summary generation error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear-all-feedback', methods=['POST'])
def clear_all_feedback():
    """
    Deletes all records from the 'responses' table and clears the Google Sheet.
    """
    try:
        # --- 1. Clear the PostgreSQL Database Table ---
        # This deletes all rows from the 'responses' table but keeps the table itself.
        db.session.query(Response).delete()
        db.session.commit()
        print("Successfully cleared all rows from the 'responses' table.")

        # --- 2. Clear the Google Sheet ---
        scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name("google_credentials.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open("AI Biostats Feedback").sheet1
        
        # Deletes all rows except for the first one (the header)
        sheet.clear() 
        # Optional: Re-add the header row after clearing
        header = ["id", "timestamp", "student_id", "question", "student_answer", "ai_feedback", "rating", "feedback_comment"]
        sheet.append_row(header)
        print("Successfully cleared the Google Sheet.")
        
        return jsonify({'status': 'success', 'message': 'All feedback data has been cleared.'}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error clearing data: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
@app.route('/api/question-details/<string:prompt_id>')
def get_question_details(prompt_id):
    # 从数据库查询，而不是读取 questions.json
    question = Question.query.filter_by(prompt_id=prompt_id).first()

    if question:
        return jsonify({
            'title': question.title,
            'question_text': question.question_text,
            'image_src': question.image_url # 注意字段名匹配
        })
    else:
        return jsonify({'error': 'Question details not found'}), 404
@app.route('/api/get-unique-problems', methods=['GET'])
def get_unique_problems():
    try:
        # 从数据库查询所有问题
        all_questions = Question.query.order_by(Question.created_at.desc()).all()

        problem_list = []
        for q in all_questions:
            problem_list.append({
                'prompt_id': q.prompt_id,
                'title': q.title
            })

        return jsonify(problem_list)

    except Exception as e:
        print(f"Error getting unique problems from DB: {e}")
        return jsonify([]), 500
@app.route('/api/create-question', methods=['POST'])
def create_question():
    # 这里之后会添加安全验证
    
    title = request.form.get('title')
    question_text = request.form.get('question_text')
    ai_prompt = request.form.get('ai_prompt')
    image_file = request.files.get('image')

    if not title or not question_text or not ai_prompt:
        return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400

    # 1. 处理图片上传
    image_url = None
    if image_file:
        try:
            # 上传到 Cloudinary
            upload_result = cloudinary.uploader.upload(image_file)
            image_url = upload_result.get('secure_url')
        except Exception as e:
            print(f"Image upload failed: {e}")
            return jsonify({'status': 'error', 'message': 'Image upload failed'}), 500

    # 2. 生成唯一的 prompt_id
    # 将标题转换为小写，替换空格为-，并移除特殊字符
    base_id = re.sub(r'[^a-z0-9-]+', '', title.lower().replace(' ', '-'))
    # 添加一个时间戳确保唯一性
    prompt_id = f"{base_id}-{int(datetime.now().timestamp())}"

    # 3. 创建新的 Question 对象并存入数据库
    new_question = Question(
        prompt_id=prompt_id,
        title=title,
        question_text=question_text,
        ai_prompt=ai_prompt,
        image_url=image_url
    )
    db.session.add(new_question)
    db.session.commit()

    # 4. 返回成功信息和新的 prompt_id
    return jsonify({
        'status': 'success',
        'message': 'Question created successfully!',
        'prompt_id': prompt_id
    })
@app.route('/create')
def create_page():
    # 这里之后会添加安全验证
    return render_template('creator.html')
if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')