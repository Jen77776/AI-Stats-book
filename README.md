# AI-Powered Tutor for Applied Biostatistics 🧪🤖

An interactive learning platform that embeds AI-driven tutor widgets directly into the *Applied Biostatistics* Quarto textbook. This project provides students with instant feedback and equips instructors with a powerful real-time analytics dashboard.



### Live Demonstrations 🚀

* **Live Quarto Book:** [https://jen77776.github.io/AI-Stats-book/](https://jen77776.github.io/AI-Stats-book/)
* **Live Instructor Dashboard:** [https://ai-stats-book.onrender.com/dashboard](https://ai-stats-book.onrender.com/dashboard)

---

## ✨ Core Features

This project enhances the learning experience with features for both students and instructors.

### For Students
* **Instant Feedback**: Get immediate, constructive feedback on open-ended questions from an AI Teaching Assistant.
* **Seamless Integration**: Interact with the tutor widget directly within the textbook chapters—no need to switch contexts.
* **Optional Anonymity**: Submit answers anonymously or provide an optional student ID.

### For Instructors
* **Real-Time Analytics Dashboard**: A comprehensive dashboard to monitor class performance and engagement.
* **Performance Overview**: Visualize student performance grades with an aggregated pie chart.
* **Feedback Quality Analysis**: Understand how students rate the AI's feedback with a bar chart overview.
* **AI-Generated Class Summaries**: Automatically generate high-level summaries that identify **common points of confusion** and highlight insightful student answers.
* **AI-Generated Answer Detection**: Automatically flag student submissions that are likely written by AI.
* **Detailed Response Log**: View and search all student submissions, AI feedback, and student ratings in a centralized table.

---

## 🛠️ Technology Stack

* **Backend**: Python, Flask, SQLAlchemy
* **Frontend**: HTML, CSS, JavaScript, Chart.js, Quarto
* **Database**: PostgreSQL (for production), SQLite (for local development)
* **AI Model**: Google Gemini 1.5 Flash
* **Deployment**: Render (for Backend & Dashboard), Quarto Pub / GitHub Pages (for Frontend Book)

---

## 📁 Project Structure

The project is structured into two main components: a Flask backend and a Quarto frontend.
```
/AI_BIOSTATS_TUTOR_PROJECT/
├── 📁 flask-backend/
│   ├── app.py                 # Main Flask application logic
│   ├── requirements.txt         # Python dependencies
│   ├── questions.json           # Stores question details (title, text, image)
│   ├── .env                     # Stores secret keys (API key, DB URI)
│   ├── google_credentials.json  # Google Service Account key
│   └── 📁 prompts/
│       └── chapter5_q8.txt      # AI prompts for specific questions
│
└── 📁 quarto-book/
    ├── index.qmd                # Example chapter with embedded widget
    ├── widget.html              # The student-facing HTML widget
    ├── widget-script.js         # Frontend logic for the widget
    ├── _quarto.yml              # Quarto book configuration
    └── ...                      # Other book files (.qmd, images, etc.)
```


---
## ⚙️ Setup and Configuration

### Prerequisites
* Python (3.9+)
* R (4.0+)
* Quarto CLI

### 1. Backend Setup (`flask-backend/`)

1.  **Create and Activate Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On macOS/Linux
    # venv\Scripts\activate   # On Windows
    ```

2.  **Install Python Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment Variables**:
    * Create a file named `.env` in the backend's root directory.
    * Add your secret keys to this file. The database URI is often provided by hosting services like Render.
        ```env
        GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
        DATABASE_URL="YOUR_POSTGRESQL_DATABASE_URI"
        ```
    * **Important**: Add `.env` to your `.gitignore` file to keep your keys secure.

### 2. Frontend Setup (`quarto-book/`)

While the widget is HTML/JS, the Quarto book may rely on R to render code chunks.

1.  **Start an R session** in your terminal by typing `R`.
2.  **Install necessary R packages** from within the R console:
    ```r
    install.packages(c("knitr", "rmarkdown", "tidyverse"))
    ```
3.  Exit R by typing `q()`.

---

## ▶️ Running the Project Locally

You'll need **two separate terminals** running at the same time.

### Terminal 1: Start the Backend Server

1.  Navigate to your backend directory (`flask-backend/`).
2.  Activate the virtual environment (`source venv/bin/activate`).
3.  Run the application. The database will be created automatically on the first run.
    ```bash
    python app.py
    ```
    The backend server will now be running on `http://127.0.0.1:5001`.

### Terminal 2: Preview the Frontend Book

1.  Navigate to your frontend directory (`quarto-book/`).
2.  Run the Quarto preview command.
    ```bash
    quarto preview
    ```
    This will open your default browser with a live preview of the textbook. Navigate to the page containing the widget to test the full application.

---

## 📝 Adding New Questions

Adding a new interactive question is a simple three-step process:

1.  **Create a Prompt File**: In the `flask-backend/prompts/` directory, create a new text file (e.g., `new_question_prompt.txt`). This file contains the instructions and rubric for the AI to grade the student's answer.

2.  **Update `questions.json`**: In the `flask-backend/` directory, add a new entry to the `questions.json` file. The key (e.g., `"new_question_prompt"`) must match the name of your new prompt file.
    ```json
    {
      "chapter5_q8": { "...": "..." },
      "new_question_prompt": {
        "title": "New Question Title",
        "question_text": "This is the text of the new question for students.",
        "image_src": "path/to/optional/image.png"
      }
    }
    ```

3.  **Embed in Quarto**: In your `.qmd` file inside the `quarto-book/` directory, embed the widget using an `iframe`, pointing to the new `prompt_id`.
    ```
    ```{=html}
    <iframe src="widget.html?prompt_id=new_question_prompt" width="100%" height="800" style="border:none;"></iframe>
    ```
    ```
