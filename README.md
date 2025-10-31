# AI-Powered Tutor for Applied Biostatistics 🧪🤖

An interactive learning platform that embeds AI-driven tutor widgets directly into the Applied Biostatistics Quarto textbook. This project provides students with instant feedback and equips instructors with a powerful, secure, real-time analytics dashboard and a seamless question management system

## Live Demonstrations 🚀

* **Live Quarto Book:** [[https://jen77776.github.io/AI-Stats-book/]](https://ybrandvain.github.io/biostats/)
* **Live Instructor Dashboard:** https://ai-stats-book.onrender.com/dashboard
* **Live Question management page:** https://ai-stats-book.onrender.com/edit-problems

## ✨ Core Features

This project enhances the learning experience with features for both students and instructors.

### For Students

* **Instant Feedback:** Get immediate, constructive feedback on open-ended questions from an AI Teaching Assistant.
* **Seamless Integration:** Interact with the tutor widget directly within the textbook chapters—no need to switch contexts.
* **Optional Anonymity:** Submit answers anonymously or provide an optional student ID.

### For Instructors
* **Secure User Authentication:** All instructor-facing pages and APIs are protected via a robust OAuth login system, ensuring your data is safe and accessible only by authorized users.
* **Web-Based Question Management:** Add, create, and manage all interactive questions through a simple, secure web interface.
* **Real-Time Analytics Dashboard:** A comprehensive dashboard to monitor class performance and engagement.
* **Performance Overview:** Visualize student performance grades with an aggregated pie chart.
* **Feedback Quality Analysis:** Understand how students rate the AI's feedback with a bar chart overview.
* **AI-Generated Class Summaries:** Automatically generate high-level summaries that identify common points of confusion and highlight insightful student answers.
* **AI-Generated Answer Detection:** Automatically flag student submissions that are likely written by AI.
* **Detailed Response Log:** View and search all student submissions, AI feedback, and student ratings in a centralized table.

## 🛠️ Technology Stack

* **Backend:** Python, Flask, SQLAlchemy
* **Authentication：** OAuth
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
│   ├── 📁 app/
│        └── __init__.py           # Application factory (create_app) and plugin initialization
│        └── models.py             # SQLAlchemy database models
│        └── services.py           # Core business logic (AI calls, Google Sheets, etc.)
│        └── 📁blueprints/      
│            └── auth_views.py     # Authentication (OAuth) and page-rendering routes
│            └── api.py            # All API routes (e.g., /api/evaluate)
│    ├── 📁 migrations/             # Alembic database migration scripts
│    ├── 📁 templates/
│         └── dashboard.html      
│         └── edit_problems.html
│         └── login.html    
│   ├── run.py                     # New application entry point
│   ├── config.py                  # Configuration classes
│   ├── .env                       # Environment variables (secret)
│   ├── google_credentials.json    # Google Sheets service account key
│   ├── requirements.txt           # Python dependencies
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
 ``ini
4.  **For local development, use SQLitev**
DATABASE_URL="sqlite:///local_db.sqlite3"

**API Keys and Credentials**
```bash
GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
CLOUDINARY_CLOUD_NAME="YOUR_CLOUDINARY_CLOUD_NAME"
CLOUDINARY_API_KEY="YOUR_CLOUDINARY_API_KEY"
CLOUDINARY_API_SECRET="YOUR_CLOUDINARY_API_SECRET"
```
**OAuth Credentials (Example for Google)**
You must create OAuth 2.0 credentials in your provider's console
```bash
GOOGLE_CLIENT_ID="YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET="YOUR_GOOGLE_CLIENT_SECRET"
SECRET_KEY="A_STRONG_RANDOM_SECRET_KEY_FOR_SESSIONS"
```

Important: Add `.env` to your `.gitignore` file to keep your keys secure.
5.  **Initialize the database and run the first migration**
```bash
flask db upgrade
```
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

1.  **Connect Repo to Render:**  Connect your GitHub repository to a new Web Service on Render.
2.  **Set Build Command:** In Render's settings, ensure the build command includes running database migrations:
     ```bash
     pip install -r requirements.txt && flask db upgrade
     ```
3. **Set Start Command:** use ```bash gunicorn "app:create_app()" ```
4.  **Set Environment Variables:** In the Render dashboard, go to the "Environment" section and add all the same keys from your `.env` file (`DATABASE_URL`, `GEMINI_API_KEY`, etc.). **Important:** For the `DATABASE_URL`, use the URL provided by Render's own PostgreSQL database service.
5.  **Auto-Deploy:** Pushing any changes to your backend's GitHub repository will automatically trigger a new deployment on Render.

### Frontend Deployment (GitHub Pages)

The frontend Quarto book is deployed automatically via GitHub Actions.

1.  **Setup Workflow (One-time only):** If you haven't set up the deployment workflow yet, navigate to your local `quarto-book` directory in the terminal and run:
    ```bash
    quarto publish gh-pages
    ```
    This will create a `.github/workflows/publish.yml` file. Add, commit, and push this file to your repository.

2.  **Auto-Deploy:** After the workflow is set up, any time you `git push` changes to your `quarto-book` repository, GitHub Actions will automatically build and deploy your site to GitHub Pages.


# How to Integrate the AI Tutor into Your Quarto Book

This guide will walk you through the simple steps required to embed the AI-Powered Tutor widget into your own Quarto textbook. This will allow you to add interactive, auto-grading questions directly into your course materials, using the existing, centralized backend service.

### Prerequisites

* A Quarto book project where you want to add the interactive widgets.

---

### Step 1: Get the Widget Files

To get started, you need two essential frontend files. These files contain the universal student-facing interface for the tutor.

1.  Obtain the following two files from the project administrator:
    * `widget.html`
    * `widget-script.js`
2.  Place both of these files in the **root directory** of your Quarto book project, alongside your `.qmd` files.

### Step 2: Create Your Questions

All question content (the text, grading rubrics, and images) is managed through a central web portal. You do not need to edit any local files to create new questions.

1.  Open your web browser and navigate to the **Question Creator page**:
    * **[https://ai-stats-book.onrender.com/create](https://ai-stats-book.onrender.com/create)**

2.  Fill out the form for each new question you want to create:
    * **Question Title:** A descriptive title for the question.
    * **Question Text:** The full text of the question as students will see it.
    * **AI Grading Instructions:** The detailed rubric and guidelines for the AI to use when evaluating student answers.
    * **Image (Optional):** You can upload an image to be displayed with the question.

3.  Click the **"Create Question"** button to save it to the central database.

### Step 3: Embed the Widget in Your Book

After you successfully create a question in the web portal, the page will automatically generate an `<iframe>` code snippet. This is the code you need to place in your book.

1.  **Copy** the entire `<iframe>` code snippet provided on the success page. It will look something like this:
    ```html
    <iframe src="widget.html?prompt_id=your-new-question-id-12345" width="100%" height="800" style="border:none;"></iframe>
    ```

2.  Open the `.qmd` chapter file where you want the question to appear.

3.  **Paste** the `<iframe>` snippet directly into the file at the desired location. Make sure it is inside a raw HTML block in your Markdown file:

    ````
    ```{=html}
    <iframe src="widget.html?prompt_id=your-new-question-id-12345" width="100%" height="800" style="border:none;"></iframe>
    ```
    ````

### Step 4: Publish Your Book

That's it! Once the `iframe` code is in place, you can preview and publish your Quarto book using your normal workflow (e.g., running `quarto publish gh-pages`). The embedded widget will automatically fetch the question content from the backend and be ready for your students to use.

---
#### An Important Note on Shared Resources

Please be aware that this service uses a centralized backend. This means all questions created by any instructor are stored in the same database. All student responses will also be visible on the central instructor dashboard, which can be accessed here:
* **Instructor Dashboard:** [https://ai-stats-book.onrender.com/dashboard](https://ai-stats-book.onrender.com/dashboard)





