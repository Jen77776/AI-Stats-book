# AI Biostats Book – Interactive Tutor Project

This project aims to integrate a series of AI-driven interactive tutor widgets into Professor Yaniv Brandvain's online textbook, *Applied Biostatistics*.

The first prototype has been completed: an **evaluative chatbot** for a data visualization problem. It receives a student's answer, provides instant feedback generated by a Large Language Model (LLM), and logs all interactions to both a local database and an online Google Sheet.

**Google Sheet Link:** [https://docs.google.com/spreadsheets/d/1jCZQq9zPbldhaNbO2VgjZaWul8wsdyp8k94SCbUrfDM/edit?gid=0#gid=0](https://docs.google.com/spreadsheets/d/1jCZQq9zPbldhaNbO2VgjZaWul8wsdyp8k94SCbUrfDM/edit?gid=0#gid=0)

---

## 📁 Project Structure

This project consists of two main components, recommended to be in separate folders:

### 🔧 Backend (Flask App)

**Example folder:** `AI_Stats_Tutor/` (or `flask-ai-feedback/`)

- `app.py`: Main Flask application.
- `requirements.txt`: Python package dependencies.
- `feedback.db`: SQLite database file.
- Handles AI logic, database interactions, and Google Sheets communication.

### 🌐 Frontend (Quarto Book Sandbox)

**Example folder:** `biostats-sandbox/`

- Contains Quarto source files (`.qmd`) and config (`_quarto.yml`).
- Embeds the AI tutor as an HTML widget in the textbook pages.

---

## ⚙️ Environment Setup

### 1. Prerequisites

Ensure the following software is installed on your system:

- Python (version 3.9 or higher)
- R (version 4.0 or higher)
- Quarto

### 2. Backend Setup

These steps should be performed in the backend project folder (e.g., `AI_Stats_Tutor/`).

1.  **Create and activate a Python virtual environment:**
    ```bash
    # Create the virtual environment
    python -m venv venv

    # Activate it
    # On macOS or Linux:
    source venv/bin/activate
    # On Windows:
    # venv\Scripts\activate
    ```

2.  **Install Python dependencies:**
    In the activated virtual environment, run the following command to install all necessary libraries from the `requirements.txt` file.
    ```bash
    pip install -r requirements.txt
    ```

### 3. Frontend Setup

Quarto requires certain R packages to render documents correctly.

1.  **Start an R session** by typing `R` in your terminal.
2.  **Install necessary R packages** by running the following command inside R:
    ```r
    install.packages(c("knitr", "rmarkdown", "tidyverse"))
    ```
3.  Exit R by typing `q()`.

---

## 🔐 Configuration

This project requires credentials for Google services. These should be stored securely and **never** be committed to Git.

### 1. Google Gemini API Key
1.  In the root of your backend folder, create a file named `.env`.
2.  Add your API key to this file in the following format:
    ```
    GEMINI_API_KEY="YOUR_ACTUAL_API_KEY_HERE"
    ```
3.  **Crucially**, ensure your `.gitignore` file contains a line for `.env` to prevent your secret key from being uploaded to GitHub.

### 2. Google Sheets API Credentials
1.  Download your `google_credentials.json` service account key file from the Google Cloud Console.
2.  Place this file in the root of your backend folder.
3.  Share your target Google Sheet with the `client_email` from the credentials file, granting it **"Editor"** access.
4.  The `.gitignore` file should also list `google_credentials.json` to keep it secure.

---

## ▶️ Running the Project

You will need **two terminal windows open simultaneously** to run the backend and frontend separately.

### Step 1: Initialize the Database
This step is only necessary on the first run or after deleting the database file.

1.  Navigate to the backend folder and activate your virtual environment.
2.  Run the database initialization command:
    ```bash
    flask --app app init-db
    ```
    You should see the message: `Initialized the database.`

### Step 2: Start Backend Server
In the same terminal, start the Flask server:
```bash
python app.py
```
The server will run on http://127.0.0.1:5000. Keep this terminal open.

Step 3: Start Frontend Preview
In a second terminal, navigate to your Quarto sandbox folder:
```bash
quarto preview
```
A browser window will open with your textbook preview. Navigate to the page with the embedded AI widget to begin testing.

✅ Current Implemented Features
Evaluative Chatbot: Provides one-shot AI-driven feedback for a data visualization problem.

Local Database Logging: Stores all interactions, including an optional student ID, in feedback.db.

Google Sheets Sync: Interactions are automatically synced to a connected Google Sheet for easy access.

Modern UI: The widget features a clean and interactive frontend design.
