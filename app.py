# pip install streamlit openai python-dateutil
# streamlit run app.py

# ============================================================================
# OPPORTUNITY SCOUT AI — SOFTEC 2026
# ============================================================================
# A complete Streamlit application that lets students paste opportunity emails
# (scholarships, internships, competitions, fellowships), extracts structured
# data using an LLM, scores each opportunity against the student's profile
# using a deterministic scoring engine, and outputs a ranked priority board
# with action checklists.
# ============================================================================

import os
import streamlit as st
import json
import re
import time
from datetime import date
from dateutil.parser import parse as parse_date
from openai import OpenAI

# ============================================================================
# DOTENV HELPER FUNCTIONS
# ============================================================================
def load_env():
    env_vars = {}
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip().strip("'\"")
    return env_vars

def save_env(env_vars):
    with open(".env", "w") as f:
        for k, v in env_vars.items():
            f.write(f"{k}={v}\n")

# ============================================================================
# PAGE CONFIG — MUST be the FIRST Streamlit call
# ============================================================================
st.set_page_config(
    page_title="Opportunity Scout AI",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================
def init_session_state():
    env_vars = load_env()
    defaults = {
        "admin_unlocked": False,
        "current_page": "scout",
        "profile": {
            "name": "",
            "degree": "BSCS",
            "semester": 4,
            "cgpa": 3.0,
            "skills_raw": "",
            "skills": [],
            "preferred_types": [],
            "financial_need": False,
            "location": "No Preference",
        },
        "email_batch": [],
        "results": [],
        "scan_complete": False,
        "api_log": [],
        "checklist_state": {},
        "api_slots": [
            {
                "label": "Groq 1 (Primary)",
                "base_url": env_vars.get("GROQ1_BASE_URL", "https://api.groq.com/openai/v1"),
                "api_key": env_vars.get("GROQ1_API_KEY", ""),
                "model": env_vars.get("GROQ1_MODEL", "llama-3.3-70b-versatile"),
                "enabled": env_vars.get("GROQ1_ENABLED", "True") == "True",
                "env_prefix": "GROQ1"
            },
            {
                "label": "Groq 2 (Fallback 1)",
                "base_url": env_vars.get("GROQ2_BASE_URL", "https://api.groq.com/openai/v1"),
                "api_key": env_vars.get("GROQ2_API_KEY", ""),
                "model": env_vars.get("GROQ2_MODEL", "llama-3.3-70b-versatile"),
                "enabled": env_vars.get("GROQ2_ENABLED", "False") == "True",
                "env_prefix": "GROQ2"
            },
            {
                "label": "OpenRouter 1 (Fallback 2)",
                "base_url": env_vars.get("OR1_BASE_URL", "https://openrouter.ai/api/v1"),
                "api_key": env_vars.get("OR1_API_KEY", ""),
                "model": env_vars.get("OR1_MODEL", "google/gemini-1.5-flash"),
                "enabled": env_vars.get("OR1_ENABLED", "True") == "True",
                "env_prefix": "OR1"
            },
            {
                "label": "OpenRouter 2 (Fallback 3)",
                "base_url": env_vars.get("OR2_BASE_URL", "https://openrouter.ai/api/v1"),
                "api_key": env_vars.get("OR2_API_KEY", ""),
                "model": env_vars.get("OR2_MODEL", "google/gemini-1.5-flash"),
                "enabled": env_vars.get("OR2_ENABLED", "False") == "True",
                "env_prefix": "OR2"
            },
            {
                "label": "Together AI (Fallback 4)",
                "base_url": env_vars.get("TOGETHER_BASE_URL", "https://api.together.xyz/v1"),
                "api_key": env_vars.get("TOGETHER_API_KEY", ""),
                "model": env_vars.get("TOGETHER_MODEL", "meta-llama/Llama-3-70b-chat-hf"),
                "enabled": env_vars.get("TOGETHER_ENABLED", "True") == "True",
                "env_prefix": "TOGETHER"
            },
            {
                "label": "Fireworks AI (Fallback 5)",
                "base_url": env_vars.get("FIREWORKS_BASE_URL", "https://api.fireworks.ai/inference/v1"),
                "api_key": env_vars.get("FIREWORKS_API_KEY", ""),
                "model": env_vars.get("FIREWORKS_MODEL", "accounts/fireworks/models/llama-v3p1-70b-instruct"),
                "enabled": env_vars.get("FIREWORKS_ENABLED", "False") == "True",
                "env_prefix": "FIREWORKS"
            },
            {
                "label": "LM Studio (Local)",
                "base_url": env_vars.get("LMSTUDIO_BASE_URL", "http://localhost:1234/v1"),
                "api_key": env_vars.get("LMSTUDIO_API_KEY", "lm-studio"),
                "model": env_vars.get("LMSTUDIO_MODEL", "local-model"),
                "enabled": env_vars.get("LMSTUDIO_ENABLED", "False") == "True",
                "env_prefix": "LMSTUDIO"
            },
        ],
        "scoring_weights": {
            "academic": 30,
            "skill": 30,
            "urgency": 25,
            "preference": 15,
        },
        "extraction_settings": {
            "max_tokens": 1500,
            "custom_system_prompt": "",
        },
    }

    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ============================================================================
# CUSTOM CSS INJECTION
# ============================================================================
def inject_css():
    primary_color = st.session_state.get("custom_primary_color", "#4f46e5")
    st.markdown(
        f"""
    <style>
    :root {{
        --primary-color: {primary_color};
    }}
    
    /* Claude Sidebar Style Overrides */
    [data-testid="stSidebar"] {{
        background-color: #1e1e1e !important;
    }}
    [data-testid="stSidebar"] * {{
        color: #e5e7eb !important;
    }}
    div[role="radiogroup"] > label > div:first-child {{
        display: none !important;
    }}
    div[role="radiogroup"] > label {{
        padding: 10px 14px;
        border-radius: 8px;
        margin-bottom: 6px;
        transition: background-color 0.2s;
        cursor: pointer;
    }}
    div[role="radiogroup"] > label:hover {{
        background-color: rgba(255, 255, 255, 0.1) !important;
    }}
    div[role="radiogroup"] > label[data-selected="true"] {{
        background-color: rgba(255, 255, 255, 0.15) !important;
        font-weight: 600;
    }}

    /* Primary button */
    .stButton > button {{
        background-color: var(--primary-color) !important;
        color: white !important;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: background-color 0.2s;
    }}
    .stButton > button:hover {{ opacity: 0.9; }}

    /* Score color bars applied via st.markdown on card containers */
    .score-green  {{ border-left: 5px solid #22c55e; padding: 12px 16px; background: color-mix(in srgb, #22c55e 10%, var(--secondary-background-color)); border-radius: 0 8px 8px 0; margin-bottom: 16px; }}
    .score-yellow {{ border-left: 5px solid #eab308; padding: 12px 16px; background: color-mix(in srgb, #eab308 10%, var(--secondary-background-color)); border-radius: 0 8px 8px 0; margin-bottom: 16px; }}
    .score-orange {{ border-left: 5px solid #f97316; padding: 12px 16px; background: color-mix(in srgb, #f97316 10%, var(--secondary-background-color)); border-radius: 0 8px 8px 0; margin-bottom: 16px; }}
    .score-red    {{ border-left: 5px solid #ef4444; padding: 12px 16px; background: color-mix(in srgb, #ef4444 10%, var(--secondary-background-color)); border-radius: 0 8px 8px 0; margin-bottom: 16px; }}

    /* Skill pills */
    .skill-pill {{
        display: inline-block;
        background: color-mix(in srgb, var(--primary-color) 20%, var(--background-color));
        color: var(--text-color);
        border: 1px solid color-mix(in srgb, var(--primary-color) 50%, var(--background-color));
        border-radius: 12px;
        padding: 2px 10px;
        margin: 2px;
        font-size: 0.85rem;
    }}

    /* App header */
    .app-header {{
        text-align: center;
        padding: 1rem 0 0.5rem 0;
        border-bottom: 1px solid var(--secondary-background-color);
    }}
    .app-header h1 {{ color: var(--primary-color); font-size: 2rem; margin: 0; }}
    .app-header p  {{ color: var(--text-color); opacity: 0.7; margin: 0; }}
    </style>
    """,
        unsafe_allow_html=True,
    )


# ============================================================================
# LLM API CALL WITH FALLBACK CHAIN
# ============================================================================
def call_llm(prompt: str, system_prompt: str = "", is_json: bool = True) -> str:
    slots = st.session_state["api_slots"]
    settings = st.session_state["extraction_settings"]
    active_slots = [s for s in slots if s["enabled"] and s["api_key"].strip()]

    if not active_slots:
        raise ValueError(
            "No API slots enabled with keys. Go to Admin Panel to configure."
        )

    for slot in active_slots:
        start = time.time()
        try:
            client = OpenAI(
                base_url=slot["base_url"].rstrip("/"),
                api_key=slot["api_key"],
            )
            sys_msg = settings["custom_system_prompt"] or system_prompt
            messages = []
            if sys_msg:
                messages.append({"role": "system", "content": sys_msg})
            messages.append({"role": "user", "content": prompt})

            kwargs = {
                "model": slot["model"],
                "messages": messages,
                "max_tokens": settings["max_tokens"],
                "temperature": 0.1 if is_json else 0.7,
            }
            if is_json:
                kwargs["response_format"] = {"type": "json_object"}

            response = client.chat.completions.create(**kwargs)
            elapsed = int((time.time() - start) * 1000)
            result = response.choices[0].message.content
            st.session_state["api_log"].insert(
                0,
                f"[{time.strftime('%H:%M:%S')}] {slot['label']} → SUCCESS ({elapsed}ms)",
            )
            st.session_state["api_log"] = st.session_state["api_log"][:20]
            return result
        except Exception as e:
            elapsed = int((time.time() - start) * 1000)
            st.session_state["api_log"].insert(
                0,
                f"[{time.strftime('%H:%M:%S')}] {slot['label']} → {type(e).__name__}: {str(e)[:80]} ({elapsed}ms)",
            )
            st.session_state["api_log"] = st.session_state["api_log"][:20]
            continue

    raise RuntimeError(
        "All API slots failed. Check the API Activity Log in the sidebar."
    )


# ============================================================================
# EXTRACTION FUNCTION
# ============================================================================
EXTRACTION_SYSTEM_PROMPT = """
You are an academic opportunity analyst. Given raw email/notice text, determine
if it contains a real opportunity (scholarship, internship, competition, 
fellowship, research position, or job opening). Extract all relevant details.

CRITICAL: Respond ONLY with a valid JSON object. No markdown fences, no 
explanation, no preamble. Your entire response must start with { and end with }.

Use this exact schema:
{
  "is_genuine_opportunity": true or false,
  "opportunity_type": "Scholarship|Internship|Competition|Fellowship|Research|Job|Other|Not an Opportunity",
  "title": "string or null",
  "organization": "string or null",
  "deadline": "YYYY-MM-DD or null",
  "eligibility": {
    "min_cgpa": number or null,
    "degree_required": "string or null",
    "semester_range": [min_int, max_int] or null,
    "other_conditions": ["string"]
  },
  "requirements": ["string — one item per required document or action step"],
  "application_link": "string or null",
  "contact_email": "string or null",
  "stipend_or_benefit": "string or null",
  "ai_reasoning": "2-3 sentence explanation: what is this opportunity, who is it for, and why might a CS/IT student care or not care?"
}
"""


def extract_opportunity(email_text: str) -> dict:
    user_prompt = f"""Analyze this email and extract structured information:

---EMAIL START---
{email_text}
---EMAIL END---
"""
    raw_response = call_llm(user_prompt, system_prompt=EXTRACTION_SYSTEM_PROMPT)

    # Attempt 1: direct JSON parse
    try:
        return json.loads(raw_response)
    except (json.JSONDecodeError, TypeError):
        pass

    # Attempt 2: regex extraction
    match = re.search(r"\{.*\}", raw_response, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except (json.JSONDecodeError, TypeError):
            pass

    # Attempt 3: safe failure dict
    return {
        "is_genuine_opportunity": False,
        "title": "Parse Error",
        "ai_reasoning": "Could not parse LLM response.",
        "opportunity_type": "Not an Opportunity",
        "deadline": None,
        "eligibility": {},
        "requirements": [],
        "application_link": None,
        "contact_email": None,
        "stipend_or_benefit": None,
        "organization": None,
    }


# ============================================================================
# SCORING ENGINE
# ============================================================================
def calculate_priority_score(
    opportunity: dict, profile: dict, weights: dict
) -> dict:
    score = {"academic": 0, "skill": 0, "urgency": 0, "preference": 0, "bonus": 0}
    matched_skills = []
    days_left = None

    # --- ACADEMIC FIT ---
    half = weights["academic"] / 2
    degree_req = (opportunity.get("eligibility") or {}).get("degree_required")
    if not degree_req or profile["degree"].lower() in degree_req.lower():
        score["academic"] += half

    min_cgpa = (opportunity.get("eligibility") or {}).get("min_cgpa")
    if min_cgpa is None or profile["cgpa"] >= min_cgpa:
        score["academic"] += half

    # --- SKILL MATCH ---
    requirements = opportunity.get("requirements") or []
    req_text = " ".join(requirements).lower()
    student_skills = [
        s.strip().lower() for s in profile.get("skills", []) if s.strip()
    ]
    if student_skills and req_text:
        for skill in student_skills:
            if skill in req_text:
                matched_skills.append(skill)
        score["skill"] = (len(matched_skills) / len(student_skills)) * weights["skill"]
    elif not req_text:
        score["skill"] = weights["skill"] * 0.5

    # --- URGENCY ---
    deadline_str = opportunity.get("deadline")
    if deadline_str:
        try:
            deadline_date = parse_date(deadline_str).date()
            days_left = (deadline_date - date.today()).days
            if days_left < 0:
                score["urgency"] = 0
            elif days_left <= 3:
                score["urgency"] = weights["urgency"]
            elif days_left <= 7:
                score["urgency"] = weights["urgency"] * 0.6
            elif days_left <= 14:
                score["urgency"] = weights["urgency"] * 0.4
            else:
                score["urgency"] = weights["urgency"] * 0.2
        except Exception:
            score["urgency"] = weights["urgency"] * 0.2
    else:
        score["urgency"] = weights["urgency"] * 0.2

    # --- PREFERENCE ---
    opp_type = opportunity.get("opportunity_type", "")
    preferred = profile.get("preferred_types", [])
    if not preferred:
        score["preference"] = weights["preference"] * 0.5
    elif opp_type in preferred:
        score["preference"] = weights["preference"]

    # --- BONUS (up to +10, not in weights) ---
    if opportunity.get("stipend_or_benefit"):
        score["bonus"] += 5
    if opportunity.get("application_link"):
        score["bonus"] += 5

    total = sum(score.values())

    if total >= 70:
        color = "green"
    elif total >= 50:
        color = "yellow"
    elif total >= 30:
        color = "orange"
    else:
        color = "red"

    return {
        "total": round(total),
        "breakdown": score,
        "matched_skills": matched_skills,
        "days_left": days_left,
        "score_color": color,
    }


# ============================================================================
# CHECKLIST GENERATION (deterministic, no LLM call)
# ============================================================================
def generate_checklist(opportunity: dict) -> list:
    steps = []

    # From requirements
    for item in opportunity.get("requirements") or []:
        steps.append(f"Prepare / obtain: {item}")

    # Application link
    app_link = opportunity.get("application_link")
    if app_link:
        steps.append(f"Submit application at: {app_link}")
    else:
        steps.append("Check email for application link")

    # Deadline reminder
    deadline = opportunity.get("deadline")
    if deadline:
        try:
            deadline_date = parse_date(deadline).date()
            dl = (deadline_date - date.today()).days
            steps.append(
                f"Set a calendar reminder: deadline is {deadline} ({dl} days left)"
            )
        except Exception:
            steps.append(f"Set a calendar reminder: deadline is {deadline}")

    # Contact email
    contact = opportunity.get("contact_email")
    if contact:
        steps.append(
            f"Email {contact} to confirm your application was received"
        )

    # Always add screenshot step
    steps.append("Take a screenshot of your submission confirmation")

    return steps[:8]


# ============================================================================
# ADMIN PANEL
# ============================================================================
def render_admin_panel():
    st.markdown(
        '<div class="app-header"><h1>Admin Panel</h1><p>Configure API keys, scoring weights, and extraction settings</p></div>',
        unsafe_allow_html=True,
    )

    # Password gate
    if not st.session_state["admin_unlocked"]:
        st.warning("This panel is password-protected.")
        pwd = st.text_input(
            "Admin Password", type="password", key="admin_pwd_input"
        )
        if st.button("Unlock", key="admin_unlock_btn"):
            if pwd == "scout2026":
                st.session_state["admin_unlocked"] = True
                st.rerun()
            else:
                st.error("Incorrect password.")
        return

    # ---- Sub-section A: API SLOTS ----
    st.subheader("LLM API Configuration (Fallback Chain)")
    st.info(
        "The app tries each enabled slot in order. If one fails (rate limit, "
        "wrong key, timeout), it moves to the next automatically."
    )

    for i, slot in enumerate(st.session_state["api_slots"]):
        with st.expander(slot["label"], expanded=(i == 0)):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.text_input(
                    "API Key",
                    value=slot["api_key"],
                    type="password",
                    key=f"key_{i}",
                )
                st.text_input(
                    "Base URL", value=slot["base_url"], key=f"url_{i}"
                )
                st.text_input(
                    "Model Name", value=slot["model"], key=f"model_{i}"
                )
            with col2:
                st.toggle(
                    "Enabled", value=slot["enabled"], key=f"enabled_{i}"
                )
            if i == 6:
                st.info(
                    "Start LM Studio → load any model → enable local server on port 1234 "
                    "→ toggle this slot ON. No real API key needed."
                )

    col_save_api, col_test_api = st.columns(2)
    with col_save_api:
        if st.button("Save API Configuration", key="save_api_btn"):
            env_dict = {}
            for i in range(len(st.session_state["api_slots"])):
                st.session_state["api_slots"][i]["api_key"] = st.session_state.get(
                    f"key_{i}", ""
                )
                st.session_state["api_slots"][i]["base_url"] = st.session_state.get(
                    f"url_{i}", ""
                )
                st.session_state["api_slots"][i]["model"] = st.session_state.get(
                    f"model_{i}", ""
                )
                st.session_state["api_slots"][i]["enabled"] = st.session_state.get(
                    f"enabled_{i}", False
                )
                
                pfx = st.session_state["api_slots"][i]["env_prefix"]
                env_dict[f"{pfx}_API_KEY"] = st.session_state["api_slots"][i]["api_key"]
                env_dict[f"{pfx}_BASE_URL"] = st.session_state["api_slots"][i]["base_url"]
                env_dict[f"{pfx}_MODEL"] = st.session_state["api_slots"][i]["model"]
                env_dict[f"{pfx}_ENABLED"] = str(st.session_state["api_slots"][i]["enabled"])

            save_env(env_dict)
            st.success("Configuration saved to .env!")

    with col_test_api:
        if st.button("Test Active Chain", key="test_api_btn"):
            try:
                result = call_llm(
                    '{"test": true}',
                    system_prompt='Reply with exactly this JSON: {"status": "pong"}',
                )
                st.success(f"Chain responded: {result}")
            except Exception as e:
                st.error(f"Test failed: {e}")

    st.divider()

    # ---- Sub-section B: SCORING WEIGHTS ----
    st.subheader("Scoring Engine Weights")
    st.info(
        "Weights must sum to 100. Bonus points (+5 each for stipend and "
        "application link) are added on top."
    )

    wcols = st.columns(4)
    weight_keys = ["academic", "skill", "urgency", "preference"]
    weight_labels = [
        "Academic Fit",
        "Skill Match",
        "Urgency",
        "Preference",
    ]
    weight_vals = {}
    for idx, (wk, wl) in enumerate(zip(weight_keys, weight_labels)):
        with wcols[idx]:
            weight_vals[wk] = st.number_input(
                wl,
                min_value=0,
                max_value=100,
                value=st.session_state["scoring_weights"][wk],
                key=f"weight_{wk}",
            )

    total_w = sum(weight_vals.values())
    if total_w != 100:
        st.warning(f"Weights sum to {total_w}, not 100. Adjust before saving.")
    else:
        st.success("Weights sum to 100")

    if st.button("Save Weights", key="save_weights_btn"):
        st.session_state["scoring_weights"] = weight_vals.copy()
        st.success("Weights saved!")

    st.divider()

    # ---- Sub-section C: EXTRACTION SETTINGS ----
    st.subheader("Extraction Settings")
    max_tokens = st.slider(
        "Max Tokens per Extraction",
        500,
        4000,
        st.session_state["extraction_settings"]["max_tokens"],
        key="ext_max_tokens",
    )
    custom_sys = st.text_area(
        "Custom System Prompt Override (optional)",
        value=st.session_state["extraction_settings"]["custom_system_prompt"],
        height=150,
        key="ext_custom_sys",
    )
    if st.button("Save Extraction Settings", key="save_ext_btn"):
        st.session_state["extraction_settings"]["max_tokens"] = max_tokens
        st.session_state["extraction_settings"]["custom_system_prompt"] = custom_sys
        st.success("Extraction settings saved!")


# ============================================================================
# PROFILE TAB
# ============================================================================
def render_profile_tab():
    st.subheader("Student Profile")
    st.caption(
        "Fill in your profile for accurate opportunity matching and scoring."
    )

    p = st.session_state["profile"]

    # Row 1
    r1c1, r1c2 = st.columns(2)
    with r1c1:
        name = st.text_input("Full Name", value=p["name"], key="prof_name")
    with r1c2:
        degree = st.selectbox(
            "Degree Program",
            ["BSCS", "BSSE", "BSAI", "BSDS", "BBA", "MBA", "Other"],
            index=["BSCS", "BSSE", "BSAI", "BSDS", "BBA", "MBA", "Other"].index(
                p["degree"]
            ),
            key="prof_degree",
        )

    # Row 2
    r2c1, r2c2 = st.columns(2)
    with r2c1:
        semester = st.slider(
            "Current Semester", 1, 8, p["semester"], key="prof_semester"
        )
    with r2c2:
        cgpa = st.number_input(
            "CGPA",
            min_value=0.0,
            max_value=4.0,
            value=float(p["cgpa"]),
            step=0.01,
            key="prof_cgpa",
        )

    # Row 3
    skills_raw = st.text_area(
        "Skills (comma-separated)",
        value=p["skills_raw"],
        placeholder="Python, SQL, Machine Learning, React, Arduino",
        key="prof_skills_raw",
    )

    # Show parsed skills as pills
    parsed_skills = [s.strip() for s in skills_raw.split(",") if s.strip()]
    if parsed_skills:
        pills_html = " ".join(
            [f'<span class="skill-pill">{s}</span>' for s in parsed_skills]
        )
        st.markdown(pills_html, unsafe_allow_html=True)

    # Row 4
    preferred_types = st.multiselect(
        "Preferred Opportunity Types",
        ["Scholarship", "Internship", "Competition", "Fellowship", "Research", "Job"],
        default=p["preferred_types"],
        key="prof_preferred",
    )

    # Row 5
    r5c1, r5c2 = st.columns(2)
    with r5c1:
        financial_need = st.toggle(
            "Financial Need", value=p["financial_need"], key="prof_finaid"
        )
    with r5c2:
        location = st.selectbox(
            "Location Preference",
            [
                "No Preference",
                "On-site Lahore",
                "On-site Any City",
                "Remote Only",
            ],
            index=[
                "No Preference",
                "On-site Lahore",
                "On-site Any City",
                "Remote Only",
            ].index(p["location"]),
            key="prof_location",
        )

    # Profile completeness bar
    filled = sum(
        [
            bool(name.strip()),
            bool(degree),
            cgpa > 0,
            len(parsed_skills) > 0,
            len(preferred_types) > 0,
        ]
    )
    completeness = filled / 5
    st.progress(completeness, text=f"Profile {int(completeness * 100)}% complete")
    if completeness < 0.6:
        st.warning("Fill out more fields to get better opportunity matching.")

    st.divider()
    st.subheader("📄 Upload CV / Documents")
    uploaded_files = st.file_uploader(
        "Upload your CV, transcripts, or certificates (PDF, PNG, JPG allowed)",
        type=["pdf", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key="prof_cv_files"
    )
    if uploaded_files:
        st.success(f"Attached {len(uploaded_files)} document(s) to your profile.")

    st.divider()
    if st.button("Save Profile", key="save_profile_btn"):
        st.session_state["profile"] = {
            "name": name.strip(),
            "degree": degree,
            "semester": semester,
            "cgpa": cgpa,
            "skills_raw": skills_raw,
            "skills": parsed_skills,
            "preferred_types": preferred_types,
            "financial_need": financial_need,
            "location": location,
        }
        st.success("Profile saved!")


# ============================================================================
# SCOUT TAB
# ============================================================================
def render_scout_tab():
    col_left, col_right = st.columns([6, 4])

    # --- LEFT COLUMN ---
    with col_left:
        st.subheader("Paste or Upload Email Content")
        st.caption(
            "Tip: You can drag and drop multiple email files (.txt, .eml) or paste raw text below."
        )

        uploaded_emails = st.file_uploader(
            "Drop Email Files here (Max 50)",
            accept_multiple_files=True,
            type=["txt", "eml"],
            key="email_file_uploader"
        )
        if uploaded_emails:
            if st.button("Add Uploaded Files to Batch", key="add_upload_btn"):
                for uploaded_file in uploaded_emails:
                    if len(st.session_state["email_batch"]) >= 50:
                        st.error("Batch full (max 50 emails). Remove some first.")
                        break
                    try:
                        content = uploaded_file.read().decode("utf-8")
                        if content.strip():
                            lines = content.strip().split("\n")
                            preview_title = uploaded_file.name
                            for l in lines:
                                if "From:" in l or "Subject:" in l:
                                    preview_title = l[:60]
                                    break
                            st.session_state["email_batch"].append({
                                "text": content.strip(),
                                "preview": preview_title,
                                "char_count": len(content.strip()),
                            })
                    except Exception as e:
                        st.error(f"Failed to read {uploaded_file.name}: {e}")
                st.success(f"Processed files! Batch now has {len(st.session_state['email_batch'])} email(s).")
                st.rerun()
                
        st.divider()

        email_input = st.text_area(
            "Or Paste Email Content Manually",
            height=200,
            placeholder="Paste the full email text here...\n\nExample:\nFrom: scholarships@hec.gov.pk\nSubject: HEC Need-Based Scholarship 2025\n\nDear Student,\n...",
            key="email_input_area",
        )

        col_add, col_clear = st.columns(2)
        with col_add:
            if st.button("Add to Batch", key="add_batch_btn"):
                if email_input.strip():
                    if len(st.session_state["email_batch"]) >= 50:
                        st.error("Batch full (max 50 emails). Remove some first.")
                    else:
                        lines = email_input.strip().split("\n")
                        preview = next(
                            (l for l in lines if l.strip()), "Email"
                        )[:60]
                        st.session_state["email_batch"].append(
                            {
                                "text": email_input.strip(),
                                "preview": preview,
                                "char_count": len(email_input.strip()),
                            }
                        )
                        st.session_state["email_input_area"] = ""
                        st.success(
                            f"Added! Batch now has {len(st.session_state['email_batch'])} email(s)."
                        )
                        st.rerun()
                else:
                    st.warning("Paste some email content first.")
        with col_clear:
            if st.button("Clear Batch", key="clear_batch_btn"):
                st.session_state["email_batch"] = []
                st.session_state["results"] = []
                st.session_state["scan_complete"] = False
                st.rerun()

        batch_count = len(st.session_state["email_batch"])
        st.caption(f"**{batch_count}/50** emails in batch")

    # --- RIGHT COLUMN ---
    with col_right:
        st.subheader("Email Batch")
        if not st.session_state["email_batch"]:
            st.info("No emails in batch yet. Add emails from the left panel.")
        else:
            for idx, email in enumerate(st.session_state["email_batch"]):
                with st.expander(
                    f"#{idx + 1} — {email['preview']}", expanded=False
                ):
                    st.caption(f"{email['char_count']} characters")
                    st.text(
                        email["text"][:200]
                        + ("..." if len(email["text"]) > 200 else "")
                    )
                    if st.button("Remove", key=f"remove_{idx}"):
                        st.session_state["email_batch"].pop(idx)
                        st.rerun()

    # --- BOTTOM: SCAN BUTTON ---
    st.divider()
    if st.session_state["email_batch"]:
        if st.button(
            "Scan All Opportunities",
            type="primary",
            use_container_width=True,
            key="scan_all_btn",
        ):
            results = []
            progress_bar = st.progress(0, text="Starting scan...")
            status_text = st.empty()
            total = len(st.session_state["email_batch"])

            for i, email in enumerate(st.session_state["email_batch"]):
                progress_bar.progress(
                    i / total,
                    text=f"Processing email {i + 1} of {total}...",
                )
                status_text.info(
                    f"Extracting: {email['preview'][:50]}..."
                )

                try:
                    with st.spinner(f"Analyzing email {i + 1}..."):
                        extracted = extract_opportunity(email["text"])
                        if extracted.get("is_genuine_opportunity"):
                            score_data = calculate_priority_score(
                                extracted,
                                st.session_state["profile"],
                                st.session_state["scoring_weights"],
                            )
                            checklist = generate_checklist(extracted)
                            results.append(
                                {
                                    **extracted,
                                    "score_data": score_data,
                                    "checklist": checklist,
                                    "original_preview": email["preview"],
                                }
                            )
                        else:
                            results.append(
                                {
                                    **extracted,
                                    "score_data": {
                                        "total": 0,
                                        "score_color": "red",
                                        "breakdown": {
                                            "academic": 0,
                                            "skill": 0,
                                            "urgency": 0,
                                            "preference": 0,
                                            "bonus": 0,
                                        },
                                        "matched_skills": [],
                                        "days_left": None,
                                    },
                                    "checklist": [],
                                    "original_preview": email["preview"],
                                }
                            )
                except Exception as e:
                    st.error(f"Failed on email {i + 1}: {e}")
                    results.append(
                        {
                            "is_genuine_opportunity": False,
                            "title": email["preview"],
                            "ai_reasoning": f"Scan failed: {str(e)}",
                            "opportunity_type": "Not an Opportunity",
                            "score_data": {
                                "total": 0,
                                "score_color": "red",
                                "breakdown": {
                                    "academic": 0,
                                    "skill": 0,
                                    "urgency": 0,
                                    "preference": 0,
                                    "bonus": 0,
                                },
                                "matched_skills": [],
                                "days_left": None,
                            },
                            "checklist": [],
                            "original_preview": email["preview"],
                        }
                    )

            progress_bar.progress(1.0, text="Scan complete!")
            status_text.success(
                f"Scanned {total} emails. Found "
                f"{sum(1 for r in results if r.get('is_genuine_opportunity'))} opportunities."
            )
            st.session_state["results"] = results
            st.session_state["scan_complete"] = True


# ============================================================================
# PRIORITY BOARD TAB
# ============================================================================
def render_board_tab():
    if not st.session_state["scan_complete"]:
        st.info(
            "👈 Go to the Scout tab, add emails, and click 'Scan All Opportunities'."
        )
        return

    results = st.session_state["results"]
    genuine = [r for r in results if r.get("is_genuine_opportunity")]
    filtered_out = [r for r in results if not r.get("is_genuine_opportunity")]
    genuine.sort(key=lambda r: r["score_data"]["total"], reverse=True)

    # --- TOP METRICS ---
    mc1, mc2, mc3, mc4 = st.columns(4)
    with mc1:
        st.metric("Total Scanned", len(results))
    with mc2:
        st.metric("Opportunities Found", len(genuine))
    with mc3:
        avg = (
            int(
                sum(r["score_data"]["total"] for r in genuine)
                / max(len(genuine), 1)
            )
            if genuine
            else 0
        )
        st.metric("Avg Score", f"{avg}/100")
    with mc4:
        valid_days = [
            r["score_data"]["days_left"]
            for r in genuine
            if r["score_data"].get("days_left") is not None and r["score_data"]["days_left"] >= 0
        ]
        nearest = min(valid_days, default=None)
        st.metric(
            "Nearest Deadline",
            f"{nearest} days" if nearest is not None else "N/A",
        )

    # --- FILTER ROW ---
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        types = list(set(r.get("opportunity_type", "") for r in genuine))
        type_filter = st.multiselect(
            "Filter by Type", types, key="board_type_filter"
        )
    with fc2:
        min_score = st.slider("Min Score", 0, 100, 0, key="board_min_score")
    with fc3:
        sort_by = st.selectbox(
            "Sort By",
            ["Score (High→Low)", "Deadline (Soonest)", "Type"],
            key="board_sort",
        )

    # Apply filters
    display = genuine[:]
    if type_filter:
        display = [r for r in display if r.get("opportunity_type") in type_filter]
    display = [r for r in display if r["score_data"]["total"] >= min_score]
    if sort_by == "Deadline (Soonest)":
        display.sort(key=lambda r: r["score_data"].get("days_left") or 9999)
    elif sort_by == "Type":
        display.sort(key=lambda r: r.get("opportunity_type", ""))
    else:
        display.sort(key=lambda r: r["score_data"]["total"], reverse=True)

    # --- OPPORTUNITY CARDS ---
    for opp_idx, opp in enumerate(display):
        color = opp["score_data"]["score_color"]
        color_hex = {
            "green": "#22c55e",
            "yellow": "#eab308",
            "orange": "#f97316",
            "red": "#ef4444",
        }[color]
        score = opp["score_data"]["total"]
        bar_filled = "█" * (score // 10)
        bar_empty = "░" * (10 - score // 10)

        st.markdown(
            f"""
        <div class="score-{color}">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <h3 style="margin:0;color:inherit;">{opp.get('title', 'Untitled')}</h3>
            <span style="color:{color_hex};font-size:1.4rem;font-weight:bold">{score}/100</span>
          </div>
          <div style="color:{color_hex};font-family:monospace">{bar_filled}{bar_empty}</div>
          <div style="opacity:0.8;font-size:0.9rem">
            {opp.get('organization', 'Unknown Org')} &nbsp;|&nbsp;
            <b style="color:{color_hex}">{opp.get('opportunity_type', '')}</b>
          </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # DETAILS ROW
        col_d, col_cgpa, col_benefit = st.columns(3)
        with col_d:
            st.markdown("**Deadline**")
            dl = opp.get("deadline")
            days = opp["score_data"].get("days_left")
            if dl:
                urgency_tag = ""
                if days is not None:
                    if days < 0:
                        urgency_tag = "EXPIRED"
                    elif days <= 3:
                        urgency_tag = "CRITICAL"
                    elif days <= 7:
                        urgency_tag = "URGENT"
                st.markdown(
                    f"**{dl}**<br>{days} days left {urgency_tag}",
                    unsafe_allow_html=True,
                )
            else:
                st.write("Not specified")
        with col_cgpa:
            st.markdown("**📚 Min CGPA**")
            min_cgpa = (opp.get("eligibility") or {}).get("min_cgpa")
            student_cgpa = st.session_state["profile"]["cgpa"]
            if min_cgpa:
                meets = "" if student_cgpa >= min_cgpa else ""
                st.markdown(
                    f"**{min_cgpa}** {meets}<br>Your CGPA: {student_cgpa}",
                    unsafe_allow_html=True,
                )
            else:
                st.write("Not specified")
        with col_benefit:
            st.markdown("**Benefit**")
            st.write(opp.get("stipend_or_benefit") or "Not specified")

        # SCORE BREAKDOWN
        with st.expander("Score Breakdown", expanded=False):
            breakdown = opp["score_data"].get("breakdown", {})
            weights = st.session_state["scoring_weights"]
            components = ["academic", "skill", "urgency", "preference", "bonus"]
            label_map = {
                "academic": "Academic Fit",
                "skill": "Skill Match",
                "urgency": "Urgency",
                "preference": "Preference",
                "bonus": "Bonus",
            }
            for component in components:
                earned = breakdown.get(component, 0)
                max_pts = weights.get(component, 10)
                pct = min(earned / max_pts, 1.0) if max_pts > 0 else 0
                col_label, col_bar, col_val = st.columns([2, 5, 1])
                with col_label:
                    st.write(label_map.get(component, component))
                with col_bar:
                    st.progress(pct)
                with col_val:
                    st.write(f"{round(earned)}/{max_pts}")

        # EVIDENCE CARD
        with st.expander("Why This Matches You", expanded=False):
            matched = opp["score_data"].get("matched_skills", [])
            if matched:
                pills = " ".join(
                    [f'<span class="skill-pill">✓ {s}</span>' for s in matched]
                )
                st.markdown(
                    f"**Matched Skills:** {pills}", unsafe_allow_html=True
                )
            else:
                st.write("No direct skill matches found.")
            st.write(f"**AI Analysis:** {opp.get('ai_reasoning', '')}")
            if opp.get("application_link"):
                st.markdown(f"[Apply Now]({opp['application_link']})")
            if opp.get("contact_email"):
                st.write(f"Contact: {opp['contact_email']}")

        # NEXT STEPS CHECKLIST
        with st.expander("Action Checklist", expanded=True):
            checklist = opp.get("checklist", [])
            title_key = (opp.get("title") or "opp")[:20].replace(" ", "_")
            for step_idx, step in enumerate(checklist):
                ck_key = f"ck_{title_key}_{step_idx}"
                if ck_key not in st.session_state["checklist_state"]:
                    st.session_state["checklist_state"][ck_key] = False
                done = st.checkbox(
                    f"Step {step_idx + 1}: {step}",
                    value=st.session_state["checklist_state"][ck_key],
                    key=f"board_ck_{opp_idx}_{step_idx}",
                )
                st.session_state["checklist_state"][ck_key] = done

            if checklist:
                done_count = sum(
                    1
                    for i in range(len(checklist))
                    if st.session_state["checklist_state"].get(
                        f"ck_{title_key}_{i}"
                    )
                )
                st.progress(
                    done_count / len(checklist),
                    text=f"{done_count}/{len(checklist)} steps completed",
                )

        st.divider()

    # --- FILTERED OUT SECTION ---
    if filtered_out:
        with st.expander(
            f"Filtered Out — Not Genuine Opportunities ({len(filtered_out)})"
        ):
            for r in filtered_out:
                st.write(
                    f"**{r.get('title') or r.get('original_preview', 'Unknown')}**"
                )
                st.caption(
                    r.get("ai_reasoning", "No reasoning available.")
                )
                st.divider()


# ============================================================================
# CHATBOT TAB
# ============================================================================
def render_chatbot_tab():
    st.subheader("AI Guide Chatbot")
    st.caption("Ask questions about opportunities, scholarships, or how to prepare your application!")
    
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
        
    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    if prompt := st.chat_input("Ask me anything..."):
        st.session_state["chat_history"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    sys_prompt = "You are a helpful academic and career guide for fresh graduates. Keep answers concise."
                    response = call_llm(prompt, system_prompt=sys_prompt, is_json=False)
                    st.markdown(response)
                    st.session_state["chat_history"].append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# ============================================================================
# SIDEBAR
# ============================================================================
def load_demo_data():
    st.session_state["profile"] = {
        "name": "Ahmed Raza",
        "degree": "BSCS",
        "semester": 5,
        "cgpa": 3.2,
        "skills_raw": "Python, Machine Learning, SQL, React",
        "skills": ["python", "machine learning", "sql", "react"],
        "preferred_types": ["Scholarship", "Internship"],
        "financial_need": True,
        "location": "No Preference",
    }
    demo_email_1 = "From: scholarships@usaid.gov.pk\nSubject: USAID Merit & Need-Based Scholarship 2025\n\nDear Student,\nThe United States Agency for International Development (USAID) invites applications for the USAID Merit-Based Scholarship Program 2025. This scholarship provides PKR 150,000 per semester for undergraduate students in Computer Science, Software Engineering, or Artificial Intelligence programs.\n\nEligibility:\n- Minimum CGPA: 3.0\n- Enrolled in Semester 3 to Semester 7\n- Demonstrated financial need\n\nRequired Documents:\n- Official transcript\n- Completed application form\n- Proof of financial need (family income certificate)\n- Two reference letters\n\nDeadline: Apply before 2025-12-20 at https://scholarships.usaid.gov.pk/apply\n\nContact: scholarships@usaid.gov.pk"
    demo_email_2 = "From: hr@techventuresLahore.com\nSubject: Paid Machine Learning Internship — Summer 2025\n\nHi,\nTech Ventures Lahore is offering a 3-month paid Machine Learning internship for university students passionate about AI.\nStipend: PKR 30,000/month\nDuration: June–August 2025\nLocation: Johar Town, Lahore (On-site)\n\nRequirements:\n- Python programming skills\n- Familiarity with scikit-learn or TensorFlow\n- Strong SQL fundamentals\n\nApply by 2025-11-30 at https://careers.techventures.pk\nNo minimum CGPA required. Semester 4+ preferred."
    demo_email_3 = "From: deals@shopmax.pk\nSubject: FLASH SALE! 70% off on all Electronics this weekend only!\nDon't miss out! This weekend only — massive discounts on laptops, phones, and accessories at ShopMax.pk. Use code FLASH70 at checkout. Visit www.shopmax.pk. Offer valid while stocks last."
    demo_email_4 = "From: talent@deepmind-labs.com\nSubject: INTERNSHIP OFFER: Research Intern (Computer Vision & Robotics)\nDear AbdurRahman, we are pleased to invite you to join the Summer 2026 Internship cohort at DeepMind. Based on your work with YOLO11 and FaceNet architectures, you have been assigned to the Perception Team. This is a 12-week remote-first position starting June 1, 2026. You will receive a monthly stipend of $5,500.00, plus a one-time equipment grant of $2,000.00 for hardware upgrades. Please sign the attached NDA and offer letter by April 28, 2026. Your primary project will involve optimizing real-time inference on edge devices (ESP32-S3). We look forward to your contributions to our neural-link initiatives."
    demo_email_5 = "From: hr@punjab-agritech.gov.pk\nSubject: JOB OPPORTUNITY: Veterinary Data Analyst (Lahore Office)\nGreetings, Punjab AgriTech is seeking a specialized individual for the role of Veterinary Data Analyst. This unique position requires a bridge between Veterinary Sciences and Data Science. You will be responsible for digitizing livestock health records and implementing predictive models for disease outbreaks in the Ravi River belt. The starting salary is Rs. 185,000 per month with full medical coverage for your family. Candidates must demonstrate proficiency in Python and SQL. Interviews will be held at our Gulberg III office on May 5, 2026. Please bring your transcript and a portfolio of any IoT-based monitoring systems you have developed."
    demo_email_6 = "From: admissions@fulbright-program.org\nSubject: SCHOLARSHIP UPDATE: Fulbright-USEFP Master’s Award 2027\nDear Applicant, we are pleased to inform you that your preliminary application for the Fulbright Scholarship has been shortlisted. This award covers 100% of tuition fees, a monthly living allowance of $2,100.00, and round-trip airfare to the United States. To proceed to the interview stage, you must submit your final GRE scores and two letters of recommendation by the deadline of August 15, 2026. Given your dual background in CS and Veterinary Sciences, we highly recommend focusing your 'Study Objective' on how AI can revolutionize animal pathology. Please use the portal link below to upload your documents."
    demo_email_7 = "From: scholarships@hec.gov.pk\nSubject: HEC Indigenous PhD Fellowship — Batch IV Announcement\nNotice: The Higher Education Commission (HEC) of Pakistan is now accepting applications for the Indigenous PhD Fellowship. This scholarship is designed for students currently enrolled in top-tier universities like Bahria University. Selected fellows will receive a monthly stipend of Rs. 45,000 and an annual book allowance of Rs. 10,000. The deadline for the online E-portal submission is May 20, 2026. Applicants must have a minimum CGPA of 3.0 and pass the HAT entry test. Please ensure your department head signs the 'Statement of Purpose' before final submission."

    st.session_state["email_batch"] = [
        {"text": demo_email_1, "preview": "From: scholarships@usaid.gov.pk", "char_count": len(demo_email_1)},
        {"text": demo_email_2, "preview": "From: hr@techventuresLahore.com", "char_count": len(demo_email_2)},
        {"text": demo_email_3, "preview": "From: deals@shopmax.pk", "char_count": len(demo_email_3)},
        {"text": demo_email_4, "preview": "From: talent@deepmind-labs.com", "char_count": len(demo_email_4)},
        {"text": demo_email_5, "preview": "From: hr@punjab-agritech.gov.pk", "char_count": len(demo_email_5)},
        {"text": demo_email_6, "preview": "From: admissions@fulbright-program.org", "char_count": len(demo_email_6)},
        {"text": demo_email_7, "preview": "From: scholarships@hec.gov.pk", "char_count": len(demo_email_7)},
    ]
    st.session_state["scan_complete"] = False
    st.session_state["results"] = []
    st.success("Demo data loaded! View it in the Scout Emails tab.")
    st.rerun()

def render_sidebar():
    import os
    if os.path.exists("media/logo.png"):
        st.sidebar.image("media/logo.png", use_container_width=True)
    else:
        st.sidebar.markdown(
            '<div class="app-header" style="border-bottom:none; margin-top:-10px;"><h2 style="color:var(--primary-color, #4f46e5);margin:0;">Opportunity Scout</h2>'
            "</div>",
            unsafe_allow_html=True,
        )

    page = st.sidebar.radio(
        "Navigation", ["My Profile", "Scout Emails", "Priority Board", "AI Guide"], key="nav_radio", label_visibility="collapsed"
    )
    st.session_state["current_page"] = page

    st.sidebar.divider()
    p = st.session_state["profile"]
    if p["name"]:
        st.sidebar.markdown(
            f"**{p['name']}** · Sem {p['semester']} · CGPA {p['cgpa']}  \n{p['degree']} · {', '.join(p['preferred_types']) or 'No preferences set'}"
        )

    st.sidebar.caption(f"Batch: {len(st.session_state['email_batch'])} emails")
    if st.session_state["scan_complete"]:
        genuine = sum(1 for r in st.session_state["results"] if r.get("is_genuine_opportunity"))
        st.sidebar.caption(f"Results: {genuine} opportunities found")

    with st.sidebar.expander("API Activity Log"):
        log = st.session_state["api_log"]
        if log:
            for entry in log[:10]:
                st.sidebar.caption(entry)
        else:
            st.sidebar.caption("No API calls yet.")


# ============================================================================
# MAIN FUNCTION
# ============================================================================
def main():
    init_session_state()
    inject_css()

    col1, col2 = st.columns([8, 2])
    with col1:
        st.markdown(
            """
        <div class="app-header" style="text-align:left; border:none; margin:0; padding:0 0 10px 0;">
          <h1 style="color:var(--primary-color, #4f46e5); margin:0;">Opportunity Scout</h1>
          <p style="color:var(--text-color); opacity:0.7; margin:0;">Paste your opportunity emails · Get ranked · Take action</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col2:
        with st.popover("⋮"):
            st.color_picker("App Color", st.session_state.get("custom_primary_color", "#4f46e5"), key="custom_primary_color")
            if st.button("Load Demo Data", use_container_width=True):
                load_demo_data()
            if st.button("Admin Panel", use_container_width=True):
                st.session_state["current_page"] = "Admin Panel"
                st.rerun()

    st.divider()

    if st.session_state.get("current_page") == "Admin Panel":
        if st.button("← Back to Scout Dashboard"):
            st.session_state["current_page"] = "Scout Emails"
            st.rerun()
        render_admin_panel()
        return

    render_sidebar()
    page = st.session_state.get("current_page", "Scout Emails")

    if page == "My Profile":
        render_profile_tab()
    elif page == "Scout Emails":
        render_scout_tab()
    elif page == "Priority Board":
        render_board_tab()
    elif page == "AI Guide" or page == "Scout":
        # Make chatbot or other function handle it
        render_chatbot_tab()

if __name__ == "__main__":
    main()
