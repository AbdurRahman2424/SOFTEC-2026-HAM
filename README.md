# Opportunity Scout AI — SOFTEC 2026

Opportunity Scout AI is a fully functional, localized Streamlit web application designed for students and fresh graduates. It accelerates the opportunity discovery process by reading chaotic emails or raw text containing information about scholarships, internships, competitions, and fellowships. It uses AI to parse out structured data, scores them based on your dynamic professional profile, and provides a curated Priority Board detailing what you should tackle next with actionable checklists and **AI-powered Auto-Apply capabilities**.

## 🌟 Key Features

1. **Intelligent Extraction:** Uses an LLM to accurately extract crucial data from messy email chains (e.g., Min CGPA, skill requirements, stipends, contact emails, deadlines, and application links).
2. **Deterministic Scoring Engine:** Ranks opportunities against your personal profile on a 100-point scale evaluating Academic Fit, Skill Matches, Urgency, and Preferences. 
3. **Background Scanning:** Your batches of emails are processed seamlessly in a background thread, allowing you to freely navigate the app, use the AI guide, or view activity logs without being blocked by loading screens.
4. **Auto-Apply Email Drafting:** Integrated directly into your action checklist, you can generate a tailored, professional email application using your profile metrics and immediately send it via your desktop's default email client.
5. **System Activity Log:** Transparent visibility into backend processes including the execution times and reliability of the API fallback chain.
6. **Robust Multi-LLM Fallback Chain:** Provides resilience by cascading through up to 7 separate API endpoints (e.g., Groq, OpenRouter, Together AI, local LM Studio). If one API rate-limits or fails, the application automatically switches to the next available and enabled slot in the chain.

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
Run the following command to install the required packages (`streamlit`, `openai`, `python-dateutil`):

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

## 📖 How to Use the Program

Opportunity Scout AI is split into several intuitive sections found in the left-hand sidebar navigation. Here is a step-by-step guide to using the program:

### 1. Setup Your API Keys (Admin Panel)
- Look at the bottom of the sidebar and click **Admin Panel**.
- **Password:** Enter the default password (`scout2026`) to unlock the panel.
- Here you can configure multiple API keys. We recommend setting up at least **Groq 1** or an **OpenRouter** key. Enable the toggle switch next to your primary choices and click **Save API Configuration**.
- *(Optional)* In this panel you can also tweak the specific token limits or customize the weights of the deterministic scoring engine.

### 2. Build Your Profile
- Navigate to the **My Profile** tab on the sidebar.
- Fill out your personal details (Name, Degree, CGPA, Current Semester).
- Carefully add your technical/soft skills (comma-separated, e.g., `Python, React, Data Analysis`). The engine looks for exact matching string segments to calculate your Skill Fit.
- Set your preferred opportunity types (Scholarship, Internship, Job, etc.).
- Click **Save Profile**.

### 3. Add and Scan Emails
- Navigate to the **Scout Emails** tab.
- You can either **Drop Email Files** (.txt or .eml) into the uploader or explicitly paste email text into the manual entry box.
- Once you click **Add to Batch**, the emails enter a holding area. You can load up to 50 emails manually, or simply click **Load Demo Data** on the sidebar to populate the system with pre-written demo opportunities.
- Click **Scan All Opportunities**. The scan runs securely in the background. You are free to switch away from this tab and monitor your background scan via the **Activity Log**.

### 4. Review Your Priority Board
- Once the background scan reaches 100%, navigate to the **Priority Board**.
- This is your personalized opportunity hub. Opportunities are ranked from highest match (Green/Yellow) to lowest match (Orange/Red). 
- Expired opportunities (where the parsed deadline evaluates to past the current date) are automatically dropped into the **Filtered Out** accordion list at the bottom of the page.
- Expand an opportunity card to view exactly **Why This Matches You** and access your **Action Checklist**.
- **Auto-Apply:** Inside the action checklist, click **Generate Email Draft via AI**. The system prepares a sophisticated response. Click **Open Default Email App & Send 🚀** to immediately port the draft over to your system email client.

### 5. AI Guide Chatbot
- Have questions about an opportunity or need general resume advice? Jump over to the **AI Guide** tab.
- This creates a conversation using your currently active LLM fallback chain. Talk to it like a standard career mentor.

### 6. Reviewing Logs
- The **Activity Log** tab displays exactly how the fallback chain interacted behind the scenes. If a scan is taking too long or failing, the Activity Log will show you which API endpoints timed out or threw errors.

---

## ⚙️ Configuration & `.env` Security

The application supports multiple API keys via its **Admin Panel**. Keys added in the UI are securely saved locally to an auto-generated `.env` file in your root folder. 

**Ensure you never leak these keys!** The project should contain a `.gitignore` file with the following lines to prevent them from landing in version control:
```text
.env
__pycache__/
.venv/
venv/
```

*(Note: As long as you launch via `streamlit run app.py` and configure keys via the Admin page UI, the system generates this file securely.)*

---

## 🔐 Admin Panel

The Admin Panel is a password-protected configuration interface accessible from the **sidebar** (bottom button labeled **Admin Panel**).

### Accessing the Admin Panel

> **Default Password: `scout2026`**

Click **Admin Panel** in the sidebar → enter the password → click **Unlock**.

---

### Section A — LLM API Configuration (Fallback Chain)

This is the core of the application's resilience. The app works through a prioritised list of up to **7 API slots**. Each slot can be individually toggled on/off. When a slot fails (rate limit, bad key, timeout), the system automatically falls through to the next enabled slot.

| Slot # | Label | Default Base URL | Default Model |
|--------|-------|-----------------|---------------|
| 1 | Groq 1 (Primary) | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile` |
| 2 | Groq 2 (Fallback 1) | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile` |
| 3 | OpenRouter 1 (Fallback 2) | `https://openrouter.ai/api/v1` | `nvidia/nemotron-3-nano-30b-a3b:free` |
| 4 | OpenRouter 2 (Fallback 3) | `https://openrouter.ai/api/v1` | `nvidia/nemotron-3-nano-30b-a3b:free` |
| 5 | Together AI (Fallback 4) | `https://api.together.xyz/v1` | `meta-llama/Llama-3-70b-chat-hf` |
| 6 | Fireworks AI (Fallback 5) | `https://api.fireworks.ai/inference/v1` | `accounts/fireworks/models/llama-v3p1-70b-instruct` |
| 7 | LM Studio (Local) | `http://localhost:1234/v1` | `local-model` |

**For each slot, you can configure:**
- **API Key** — your secret key from the respective provider
- **Base URL** — the OpenAI-compatible endpoint for that provider
- **Model Name** — the exact model identifier string

After editing, click **Save API Configuration**. This writes all values securely to your local `.env` file.

You can also click **Test Active Chain** to send a ping request through the chain and confirm it is working before running a real scan.

> **Tip for LM Studio (Slot 7):** Start LM Studio → load any model → enable the local server on port 1234 → toggle the slot ON. The API key field can be left as `lm-studio`.

---

### Section B — Scoring Engine Weights

Control how much each factor contributes to an opportunity's final score (out of 100):

| Weight | Description | Default |
|--------|-------------|---------|
| **Academic Fit** | Degree and CGPA match | 30 |
| **Skill Match** | How many of your skills appear in requirements | 30 |
| **Urgency** | How close the deadline is | 25 |
| **Preference** | Whether the type matches your preferred types | 15 |

> **Bonus Points** (not part of the 100): +5 if a stipend/benefit is listed, +5 if an application link is present (max +10).

Weights must sum to exactly **100** before you can save. Click **Save Weights** to apply.

---

### Section C — Extraction Settings

| Setting | Description | Default |
|---------|-------------|---------|
| **Max Tokens per Extraction** | Token budget for each LLM extraction call | `1500` |
| **Custom System Prompt Override** | Replaces the built-in extraction prompt entirely (advanced) | *(empty)* |

Click **Save Extraction Settings** to apply to future scans.

---

## 💡 Tech Stack
- **Frontend & App Logic:** [Streamlit](https://streamlit.io/)
- **Data & Date Operations:** Python `json`, `datetime`, and `python-dateutil`
- **Generative AI Backend:** `openai` Python SDK (targeting standard OpenAPI interfaces like Groq and OpenRouter) 
- **Threading:** Python `threading` paired with Streamlit context management for background processing.