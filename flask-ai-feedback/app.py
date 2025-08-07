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


load_dotenv()
app = Flask(__name__, instance_relative_config=True, template_folder='templates')
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
print(f"--- DATABASE URI IN USE: {app.config['SQLALCHEMY_DATABASE_URI']} ---")

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


# def get_dataviz_feedback(student_answer):
#     if not model:
#         return "AI model failed to load."
    
#     # Prompt
#     system_prompt = """
#     You are an evaluative AI giving concise, helpful, and honest feedback on a student's written answer to a data visualization critique prompt.

#     The question is:
#     "I stole this figure from a company selling a data viz class. Examine their plot and find at least three bad data viz practices. Then say which one you think is the worst and why."

#     The figure being critiqued includes multiple design problems. The worst offense is the irregular y-axis scaling: it uses evenly spaced visual intervals with values like 10M, 50M, 200M, 250M, and 275M, which is misleading and nonsensical.

#     Other issues include:
#     - Y-axis likely doesn’t start at zero
#     - Last bar (Q1P, likely a projection) isn’t visually distinguished from observed values
#     - Arbitrary curve overlays the bars with no rationale
#     - Bars are shaded with a distracting color gradient
#     - Axis labels are small and hard to read
#     - X and Y axes have no title
#     - Font and spacing choices make interpretation harder

#     ---
#     ### Your Role:
#     - Evaluate how well the student identifies problems in the plot
#     - Give a one-off piece of feedback (not a chat), written in a warm and encouraging tone
#     - Be concise, direct, and helpful — no generic praise
#     - Your goal is not to assign a grade but to help students reflect and improve
#     - You should use an internal rubric with levels like:
#       * Great answer
#       * Good answer
#       * Thinking start
#       * Too superficial
#       * Misunderstood / incorrect
#     ---
#     ### Response Guidelines:
#     - If the student gave a great answer, affirm their reasoning and note what they did well.
#     - If the student missed key issues (especially the irregular y-axis), point that out clearly, explain why it matters, and optionally give stronger examples they could have raised.
#     - If their answer was vague or off-base, help them understand why and give a couple of clear, grounded examples they could have used.
#     - Do not say “this is a great answer but…” if the answer wasn’t great.
#     - Focus on useful and honest feedback, not on grading tone.
#     """

#     prompt = f"{system_prompt}\n\nThe student's answer is:\n\"{student_answer}\""
    
#     try:
#         response = model.generate_content(prompt)
#         return response.text
#     except Exception as e:
#         print(f"Error calling Gemini API for dataviz: {e}")
#         return "Sorry, an error occurred while getting feedback from the AI."

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

# @app.route('/api/evaluate-dataviz', methods=['POST'])
# def handle_dataviz_evaluation():
#     data = request.get_json()
#     student_answer = data.get('answer')
#     student_id = data.get('student_id', 'anonymous')
#     ai_feedback = get_dataviz_feedback(student_answer)

#     try:
#         new_response = Response(
#             student_id=student_id,
#             question="Critique of misleading data visualization (Figure 5)",
#             student_answer=student_answer,
#             ai_feedback=ai_feedback,
#             timestamp=datetime.now()
#         )
#         db.session.add(new_response)
#         db.session.commit()

#         # 只有在数据库写入成功后，才继续写入Google Sheet
#         row_to_insert = [new_response.id, str(new_response.timestamp), student_id, new_response.question, student_answer, ai_feedback, "", ""]
#         append_to_google_sheet(row_to_insert)

#         return jsonify({'feedback': ai_feedback, 'response_id': new_response.id})

#     except Exception as e:
#         # 如果数据库操作失败，回滚所有改动
#         db.session.rollback()
#         # 在终端打印出详细的错误信息
#         print(f"--- DATABASE WRITE FAILED ---: {e}")
#         # 仍然返回一个看起来“成功”的响应给前端，但附带错误信息
#         return jsonify({
#             'feedback': ai_feedback, 
#             'response_id': None,
#             'error': 'Database write operation failed.'
#         }), 500
@app.route('/api/evaluate', methods=['POST'])
def handle_evaluation():
    data = request.get_json()
    student_answer = data.get('answer')
    student_id = data.get('student_id', 'anonymous')
    prompt_id = data.get('prompt_id') # 前端需要传来这个ID

    if not prompt_id:
        return jsonify({'error': 'A prompt_id must be provided.'}), 400

    ai_feedback = get_generic_feedback(prompt_id, student_answer)
    
    new_response = Response(
        student_id=student_id,
        question=prompt_id, # 用prompt_id作为问题的标识
        student_answer=student_answer,
        ai_feedback=ai_feedback,
        timestamp=datetime.now()
    )
    db.session.add(new_response)
    db.session.commit()

    row_to_insert = [new_response.id, str(new_response.timestamp), student_id, new_response.question, student_answer, ai_feedback, "", ""]
    append_to_google_sheet(row_to_insert)

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
    responses = Response.query.order_by(Response.timestamp.desc()).all()
    output = []
    for r in responses:
        output.append({
            'id': r.id, 'student_id': r.student_id, 'question': r.question,
            'student_answer': r.student_answer, 'ai_feedback': r.ai_feedback,
            'timestamp': r.timestamp.isoformat(), 'rating': r.rating,
            'feedback_comment': r.feedback_comment
        })
    return jsonify(output)

@app.route('/api/get-summary', methods=['GET'])
def get_summary():
    """API endpoint to generate an AI-powered summary of all answers."""
    # 使用SQLAlchemy查询
    responses = Response.query.filter(Response.student_answer != '').all()
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


if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')