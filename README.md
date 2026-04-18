# Opportunity Scout AI

Opportunity Scout AI is a fully localized Streamlit application designed for students and fresh graduates. It accelerates the opportunity discovery process by reading chaotic emails or raw text containing information about scholarships, internships, competitions, and fellowships. It uses AI to parse out structure, score them against your dynamic professional profile, and provide a curated Priority Board detailing what you should tackle next with actionable checklists.

## Features

- **Profile Builder**: Input your degree, semester, CGPA, skills, and preferences to anchor the AI's recommendations natively to your background.
- **Bulk Email Parsing**: Drag-and-drop multiple `.txt` or `.eml` raw emails directly into the batch.
- **Deterministic AI Scoring**: Uses LLMs for extraction, but routes the opportunity against a transparent deterministic scoring engine evaluating Academic Fit, Skill Match, Urgency, and Preferences.
- **AI Guide**: An interactive chat assistant to ask questions regarding application preparation natively using your stored credentials and history.
- **LLM Fallback Chain**: Flexible LLM architecture allowing cascading API keys (e.g., Groq, OpenRouter, Together AI, Fireworks AI) and even isolated local servers like LM Studio.

---

## 🛠 Prerequisites & Installation

### 1. Clone the repository
```bash
git clone https://github.com/your-username/Opportunity-Scout-AI.git
cd Opportunity-Scout-AI
```

### 2. Set up a Virtual Environment (Recommended)

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
Run the following command to install the required Python packages:

```bash
pip install -r requirements.txt
```

---

## 🚀 Running the Application

Once your dependencies are installed, you can start the application with a single Streamlit command. Streamlit will boot the local web server and open a tab automatically in your browser.

```bash
streamlit run app.py
```

---

## ⚙️ Configuration & `.env` Security

The application supports multiple LLM API keys via its **Admin Panel**. 
Keys added in the UI are securely saved locally to an auto-generated `.env` file in the root directory. To protect your API tokens from accidental uploads:

Ensure your project contains a `.gitignore` file with the following lines:
```text
.env
__pycache__/
.venv
venv/
```
*(Note: As long as you launch via `streamlit run app.py`, the system is designed to generate out configuration values into the `.env` securely).*

---

## 💡 Tech Stack
- **Frontend & App Logic:** [Streamlit](https://streamlit.io/)
- **Data & Date Operations:** Python `json`, `datetime`, and `python-dateutil`
- **Generative AI Backend:** `openai` Python SDK (targeting varied LLM endpoints)

Enjoy accelerating your tech career with Opportunity Scout AI!