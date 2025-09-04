# AI-Powered Tutor for Applied Biostatistics 🧪🤖

An interactive learning platform that embeds AI-driven tutor widgets directly into the *Applied Biostatistics* Quarto textbook. This project provides students with instant feedback and equips instructors with a powerful real-time analytics dashboard and a seamless question management system.

## Live Demonstrations 🚀

* **Live Quarto Book:** https://jen77776.github.io/AI-Stats-book/
* **Live Instructor Dashboard:** https://ai-stats-book.onrender.com/dashboard

## ✨ Core Features

This project enhances the learning experience with features for both students and instructors.

### For Students

* **Instant Feedback:** Get immediate, constructive feedback on open-ended questions from an AI Teaching Assistant.
* **Seamless Integration:** Interact with the tutor widget directly within the textbook chapters—no need to switch contexts.
* **Optional Anonymity:** Submit answers anonymously or provide an optional student ID.

### For Instructors

* **Web-Based Question Management:** Add, create, and manage all interactive questions through a simple, password-protected web interface. No more editing files manually!
* **Real-Time Analytics Dashboard:** A comprehensive dashboard to monitor class performance and engagement.
* **Performance Overview:** Visualize student performance grades with an aggregated pie chart.
* **Feedback Quality Analysis:** Understand how students rate the AI's feedback with a bar chart overview.
* **AI-Generated Class Summaries:** Automatically generate high-level summaries that identify common points of confusion and highlight insightful student answers.
* **AI-Generated Answer Detection:** Automatically flag student submissions that are likely written by AI.
* **Detailed Response Log:** View and search all student submissions, AI feedback, and student ratings in a centralized table.

## 🛠️ Technology Stack

* **Backend:** Python, Flask, SQLAlchemy
* **Frontend:** HTML, CSS, JavaScript, Chart.js, Quarto
* **Database:** PostgreSQL (for production), SQLite (for local development)
* **AI Model:** Google Gemini 1.5 Flash
* **Image Storage:** Cloudinary
* **Deployment:** Render (for Backend), GitHub Pages (for Frontend Book)

## 📁 Project Structure

The project is structured into two main components: a Flask backend and a Quarto frontend. The backend now handles all question content, eliminating the need for local prompt files.
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

**Prerequisites**

* Python (3.9+)
* Quarto CLI

### 1. Backend Setup (`flask-backend/`)

1.  **Create and Activate Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On macOS/Linux
    # venv\Scripts\activate   # On Windows
    ```

2.  **Install Python Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment Variables:**
    Create a file named `.env` in the backend's root directory and add your secret keys.
    ```ini
    # For local development, use SQLite
    DATABASE_URL="sqlite:///local_db.sqlite3"

    # API Keys and Credentials
    GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
    CLOUDINARY_CLOUD_NAME="YOUR_CLOUDINARY_CLOUD_NAME"
    CLOUDINARY_API_KEY="YOUR_CLOUDINARY_API_KEY"
    CLOUDINARY_API_SECRET="YOUR_CLOUDINARY_API_SECRET"

    # Credentials for the protected /create page
    ADMIN_USER="your_admin_username"
    ADMIN_PASS="your_strong_password"
    ```
    **Important:** Add `.env` to your `.gitignore` file to keep your keys secure.

## ▶️ Running the Project Locally

You'll need **two separate terminals** running at the same time.

#### Terminal 1: Start the Backend Server

1.  Navigate to your backend directory (`flask-backend/`).
2.  Activate the virtual environment (`source venv/bin/activate`).
3.  Run the application. The database will be created automatically on the first run.
    ```bash
    python app.py
    ```
    The backend server will now be running on `http://127.0.0.1:5001`.

#### Terminal 2: Preview the Frontend Book

1.  Navigate to your frontend directory (`quarto-book/`).
2.  Run the Quarto preview command.
    ```bash
    quarto preview
    ```
    This will open your default browser with a live preview of the textbook.

## 📝 Adding New Questions (The New Way)

Adding a new interactive question is now a simple web-based process:

1.  **Launch the Creator Page:** With your local backend server running, navigate to the password-protected creator page in your browser: `http://127.0.0.1:5001/create`.
2.  **Fill in the Details:** Enter the question title, the text students will see, the grading instructions for the AI, and optionally upload an image.
3.  **Generate `iframe` Code:** Click "Create Question." The page will provide you with a ready-to-use `<iframe>` code snippet.
4.  **Embed in Quarto:** Copy the generated `<iframe>` code and paste it into the desired location in your `.qmd` file.
5.  **Preview and Publish:** Your local Quarto preview will automatically update to show the new question.

## 🚀 Deployment

The project has two parts that are deployed independently.

### Backend Deployment (Render)

1.  **Connect Repo to Render:** Connect the GitHub repository for your `flask-backend` to a new Web Service on Render.
2.  **Set Environment Variables:** In the Render dashboard, go to the "Environment" section and add all the same keys from your `.env` file (`DATABASE_URL`, `GEMINI_API_KEY`, etc.). **Important:** For the `DATABASE_URL`, use the URL provided by Render's own PostgreSQL database service.
3.  **Auto-Deploy:** Pushing any changes to your backend's GitHub repository will automatically trigger a new deployment on Render.

### Frontend Deployment (GitHub Pages)

The frontend Quarto book is deployed automatically via GitHub Actions.

1.  **Setup Workflow (One-time only):** If you haven't set up the deployment workflow yet, navigate to your local `quarto-book` directory in the terminal and run:
    ```bash
    quarto publish gh-pages
    ```
    This will create a `.github/workflows/publish.yml` file. Add, commit, and push this file to your repository.

2.  **Auto-Deploy:** After the workflow is set up, any time you `git push` changes to your `quarto-book` repository, GitHub Actions will automatically build and deploy your site to GitHub Pages.








