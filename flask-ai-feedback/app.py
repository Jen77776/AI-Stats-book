# app.py
import sqlite3
import random
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os 
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv 
load_dotenv() 
app = Flask(__name__)
CORS(app)

# --- Key Information ---
# Warning: For security reasons, API keys should not be hard-coded.
# In a real deployment, use environment variables or a secure key management service.
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
DB_PATH = os.path.join(app.instance_path, 'feedback.db')

try:
    os.makedirs(app.instance_path, exist_ok=True)
except OSError:
    pass

try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    print(f"API configuration failed: {e}")
    model = None

BIOSTAT_QUESTIONS = [
    "What is the primary purpose of the `t.test()` function in R? Please provide a simple example.",
    "In R, what does a `p-value` of less than 0.05 typically signify in the context of hypothesis testing?",
    "How would you use the `ggplot2` package in R to create a simple scatter plot showing the relationship between two variables?",
    "When conducting a linear regression analysis in R, what do the 'Coefficients' in the output of the `lm()` function represent?",
    "Please describe the main differences between a data frame and a matrix in the R language."
]

def init_db():
    conn = sqlite3.connect('feedback.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            question TEXT NOT NULL,
            student_answer TEXT NOT NULL,
            ai_feedback TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            rating INTEGER,
            feedback_comment TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.cli.command("init-db")
def init_db_command():
    """clear existing data and initialize the database."""
    init_db()
    print("Initialized the database.")

@app.route('/api/get-question', methods=['GET'])
def get_question():
    question = random.choice(BIOSTAT_QUESTIONS)
    return jsonify({'question': question})

def get_ai_feedback(question, student_answer):
    if not model:
        return "AI model failed to load."
    system_prompt = f"""
    You are an expert Teaching Assistant for an 'Applied Biostatistics with R' course.
    Your task is to evaluate a student's answer based on a specific question.
    Provide constructive, helpful, and encouraging feedback in English.
    First, briefly state if the core of the answer is correct or incorrect.
    Then, explain why and provide the correct, ideal answer with R code examples if necessary.

    The question was: "{question}"
    """
    prompt = f"{system_prompt}\n\nThe student's answer is:\n\"{student_answer}\""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return "Sorry, an error occurred while getting feedback from the AI."

@app.route('/api/feedback', methods=['POST'])
def handle_feedback_request():
    data = request.get_json()
    if not data or 'answer' not in data or 'question' not in data:
        return jsonify({'error': 'Request must include both "question" and "answer"'}), 400
    student_answer = data['answer']
    question = data['question']
    ai_feedback = get_ai_feedback(question, student_answer)
    try:
        conn = sqlite3.connect('feedback.db')
        c = conn.cursor()
        c.execute(
            "INSERT INTO responses (question, student_answer, ai_feedback, timestamp) VALUES (?, ?, ?, ?)",
            (question, student_answer, ai_feedback, datetime.now())
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database write error: {e}")
    return jsonify({'feedback': ai_feedback})


def get_dataviz_feedback(student_answer):
    if not model:
        return "AI model failed to load."
    
    # Prompt
    system_prompt = """
    You are an evaluative AI giving concise, helpful, and honest feedback on a student's written answer to a data visualization critique prompt.

    The question is:
    "I stole this figure from a company selling a data viz class. Examine their plot and find at least three bad data viz practices. Then say which one you think is the worst and why."

    The figure being critiqued includes multiple design problems. The worst offense is the irregular y-axis scaling: it uses evenly spaced visual intervals with values like 10M, 50M, 200M, 250M, and 275M, which is misleading and nonsensical.

    Other issues include:
    - Y-axis likely doesn’t start at zero
    - Last bar (Q1P, likely a projection) isn’t visually distinguished from observed values
    - Arbitrary curve overlays the bars with no rationale
    - Bars are shaded with a distracting color gradient
    - Axis labels are small and hard to read
    - X and Y axes have no title
    - Font and spacing choices make interpretation harder

    ---
    ### Your Role:
    - Evaluate how well the student identifies problems in the plot
    - Give a one-off piece of feedback (not a chat), written in a warm and encouraging tone
    - Be concise, direct, and helpful — no generic praise
    - Your goal is not to assign a grade but to help students reflect and improve
    - You should use an internal rubric with levels like:
      * Great answer
      * Good answer
      * Thinking start
      * Too superficial
      * Misunderstood / incorrect
    ---
    ### Response Guidelines:
    - If the student gave a great answer, affirm their reasoning and note what they did well.
    - If the student missed key issues (especially the irregular y-axis), point that out clearly, explain why it matters, and optionally give stronger examples they could have raised.
    - If their answer was vague or off-base, help them understand why and give a couple of clear, grounded examples they could have used.
    - Do not say “this is a great answer but…” if the answer wasn’t great.
    - Focus on useful and honest feedback, not on grading tone.
    """

    prompt = f"{system_prompt}\n\nThe student's answer is:\n\"{student_answer}\""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error calling Gemini API for dataviz: {e}")
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

@app.route('/api/evaluate-dataviz', methods=['POST'])
def handle_dataviz_evaluation():
    data = request.get_json()
    student_answer = data.get('answer')
    student_id = data.get('student_id', 'anonymous')
    ai_feedback = get_dataviz_feedback(student_answer)
    question_text = "Critique of misleading data visualization (Figure 5)"
    timestamp = datetime.now()
    response_id = None # Initialize response_id

    # 1. Write initial data to SQLite
    try:
        conn = sqlite3.connect('feedback.db')
        c = conn.cursor()
        c.execute(
            "INSERT INTO responses (student_id, question, student_answer, ai_feedback, timestamp) VALUES (?, ?, ?, ?, ?)",
            (student_id, question_text, student_answer, ai_feedback, timestamp)
        )
        response_id = c.lastrowid # Get the ID of the row we just inserted
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database write error: {e}")

    # 2. Write initial data to Google Sheet
    # The new row will have empty placeholders for the rating and comment
    row_to_insert = [response_id, str(timestamp), student_id, question_text, student_answer, ai_feedback, "", ""]
    append_to_google_sheet(row_to_insert)

    # Return the feedback AND the new ID to the frontend
    return jsonify({'feedback': ai_feedback, 'response_id': response_id})

# --- Add the new endpoint for receiving ratings ---
@app.route('/api/rate-feedback', methods=['POST'])
def rate_feedback():
    data = request.get_json()
    response_id = data.get('response_id')
    rating = data.get('rating')
    comment = data.get('comment', '')

    # 1. Update the record in the SQLite database
    try:
        conn = sqlite3.connect('feedback.db')
        c = conn.cursor()
        c.execute(
            "UPDATE responses SET rating = ?, feedback_comment = ? WHERE id = ?",
            (rating, comment, response_id)
        )
        conn.commit()

        # Fetch the entire updated row to sync with Google Sheets
        updated_row_cursor = c.execute("SELECT * FROM responses WHERE id = ?", (response_id,))
        full_updated_row = updated_row_cursor.fetchone()
        conn.close()

        # 2. Update the corresponding row in the Google Sheet
        if full_updated_row:
            # Convert the database tuple to a list of strings for gspread
            update_gsheet_row(response_id, [str(item) for item in full_updated_row])

        return jsonify({'status': 'success'}), 200
    except Exception as e:
        print(f"Rating submission error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/get-all-feedback', methods=['GET'])
def get_all_feedback():
    """API endpoint to get all feedback data from the database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM responses ORDER BY timestamp DESC")
        rows = c.fetchall()
        conn.close()
        return jsonify([dict(row) for row in rows])
    except Exception as e:
        print(f"Dashboard data fetch error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/get-summary', methods=['GET'])
def get_summary():
    """API endpoint to generate an AI-powered summary of all answers."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT student_answer FROM responses WHERE student_answer != ''")
        answers = c.fetchall()
        conn.close()

        if not answers:
            return jsonify({'summary': 'Not enough data to generate a summary.'})

        all_answers_text = "\n\n---\n\n".join([ans[0] for ans in answers])

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
        summary_response = model.generate_content(summary_prompt)
        return jsonify({'summary': summary_response.text})
    except Exception as e:
        print(f"Summary generation error: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')