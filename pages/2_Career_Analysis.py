import streamlit as st
import os
import logging
import requests

from dotenv import load_dotenv
from database import save_analysis
from application_manager import add_application
from pdf_reader import extract_text_from_pdf
from ai_analysis import analyze_resume
from github_analyzer import analyze_github

# =====================================================
# ENVIRONMENT
# =====================================================

load_dotenv()

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")

# =====================================================
# LOGGING
# =====================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CareerLensAI")

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Career Analysis",
    page_icon="📊",
    layout="wide"
)

# =====================================================
# CHECK AUTHENTICATION
# =====================================================

# Check if user is logged in
if "user" not in st.session_state or st.session_state.user is None:
    st.error("⚠️ Please log in first to access this page.")
    
    # FIX: Use st.page_link instead of st.switch_page
    st.page_link("app.py", label="Go to Login", icon="🔐")
    
    # Or use a button with rerun
    if st.button("Go to Login", use_container_width=True):
        st.session_state.page = "login"
        st.rerun()
    
    st.stop()  # Stop execution if not logged in

# =====================================================
# STYLING
# =====================================================

st.markdown(
    """
<style>
.stApp {
    background: #070B14;
    color: #E2E8F0;
}
.card {
    background: #111827;
    border: 1px solid #1E293B;
    border-radius: 18px;
    padding: 22px;
    margin-bottom: 18px;
    animation: fadeInUp 0.6s ease-out;
}
h1, h2, h3 {
    color: #F8FAFC;
}
.stButton button {
    background: #03045E !important;
    color: white !important;
    border-radius: 12px !important;
    transition: all 0.3s ease !important;
}
.stButton button:hover {
    background: #023E8A !important;
    transform: scale(1.05) !important;
}
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
</style>
""",
    unsafe_allow_html=True
)

# =====================================================
# N8N EVENT HELPER
# =====================================================

def trigger_n8n(event, data=None):
    if not N8N_WEBHOOK_URL:
        return False
    
    payload = {"event": event, **(data or {})}
    
    try:
        response = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=10)
        return response.status_code in [200, 201, 202]
    except Exception as e:
        logger.warning(f"n8n trigger failed: {e}")
        return False

# =====================================================
# SESSION STATE
# =====================================================

DEFAULT_STATE = {
    "analysis": None,
    "resume_text": "",
    "job_description": "",
    "github_data": None
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value

# =====================================================
# HEADER
# =====================================================

st.markdown(
    """
<div class="card">
    <h1>📊 Career Analysis</h1>
    <p>Upload your resume and get AI-powered career insights</p>
</div>
""",
    unsafe_allow_html=True
)

# =====================================================
# USER INFO
# =====================================================

# Show user info
user_name = st.session_state.get("user_name", "User")
user_email = st.session_state.get("user_email", "")

st.write(f"👋 Welcome, **{user_name}**!")

# =====================================================
# INPUT SECTION
# =====================================================

st.header("Candidate Profile")

col1, col2 = st.columns(2)

with col1:
    uploaded_file = st.file_uploader(
        "Upload Resume PDF",
        type=["pdf"]
    )

with col2:
    github_url = st.text_input(
        "GitHub Profile URL",
        placeholder="https://github.com/username"
    )

job_description = st.text_area(
    "Target Job Description",
    height=260
)

# =====================================================
# RESUME EXTRACTION
# =====================================================

resume_text = ""

if uploaded_file:
    try:
        resume_text = extract_text_from_pdf(uploaded_file)
        st.success("✅ Resume extracted successfully")
    except Exception as e:
        st.error(f"❌ Resume extraction failed: {e}")

# =====================================================
# ANALYSIS FUNCTION
# =====================================================

def run_analysis():
    if not resume_text:
        st.warning("Please upload resume first.")
        return
    
    if not job_description.strip():
        st.warning("Please enter job description.")
        return
    
    github_data = None
    
    if github_url:
        username = github_url.rstrip("/").split("/")[-1]
        with st.spinner("Analyzing GitHub profile..."):
            github_data = analyze_github(username)
    
    with st.spinner("Generating AI career report..."):
        result = analyze_resume(
            resume_text,
            job_description,
            github_data
        )
    
    logger.info(f"Analysis result: {result}")
    
    if result.get("error"):
        if result.get("quota_error") or "quota" in str(result.get("error", "")).lower():
            st.error(
                "⚠️ **AI Service Unavailable**\n\n"
                "The analysis service has reached its daily limit. Please try again later."
            )
        else:
            st.error(f"❌ {result.get('error')}")
        return
    
    st.session_state.analysis = result
    st.session_state.resume_text = resume_text
    st.session_state.job_description = job_description
    st.session_state.github_data = github_data
    
    trigger_n8n(
        "career_analysis_completed",
        {
            "company": result.get("company_name", ""),
            "match_score": result.get("match_score", 0)
        }
    )
    
    st.success("✅ Career analysis completed 🚀")

# =====================================================
# RUN BUTTON
# =====================================================

if st.button("Analyze Career Profile 🚀", use_container_width=True):
    run_analysis()

# =====================================================
# REPORT SECTION
# =====================================================

if st.session_state.analysis:
    analysis = st.session_state.analysis
    
    st.divider()
    st.header("Career Readiness Report")
    
    # Metrics
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.metric(
            "Job Match",
            f"{analysis.get('match_score', 0)}%"
        )
    
    with c2:
        st.metric(
            "GitHub Score",
            f"{analysis.get('github_review', {}).get('score', 0)}/100"
        )
    
    with c3:
        st.metric(
            "Candidate Level",
            analysis.get("candidate_level", "N/A")
        )
    
    st.divider()
    
    tabs = st.tabs([
        "📌 Skills Analysis",
        "🐙 GitHub Review",
        "🌎 Open Source",
        "🧭 Career Mentor"
    ])
    
    # Skills Analysis
    with tabs[0]:
        requirements = analysis.get("requirement_analysis", [])
        
        if not requirements:
            st.info("No skill analysis available.")
        else:
            for item in requirements:
                skill = item.get("skill", "Skill")
                status = item.get("status", "")
                
                if status == "strong_match":
                    icon = "🟢"
                elif status == "partial_match":
                    icon = "🟡"
                else:
                    icon = "🔴"
                
                st.markdown(f"""
### {icon} {skill}

**Status:** {status.replace('_', ' ').title()}

**Evidence**
{item.get('evidence', '')}
""")
                
                if status != "strong_match":
                    missing = item.get("missing", "")
                    next_step = item.get("next_step", "")
                    
                    if missing:
                        st.markdown(f"**Missing:** {missing}")
                    
                    if next_step:
                        st.markdown(f"**Next Step:** {next_step}")
    
    # GitHub Review
    with tabs[1]:
        github = analysis.get("github_review", {})
        st.subheader(f"GitHub Score: {github.get('score', 0)}/100")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("### Strengths")
            strengths = github.get("strengths", [])
            if strengths:
                for item in strengths:
                    st.success(item)
            else:
                st.info("No strengths found.")
        
        with col2:
            st.write("### Improvement Areas")
            weaknesses = github.get("weaknesses", [])
            if weaknesses:
                for item in weaknesses:
                    st.warning(item)
            else:
                st.info("No weaknesses found.")
    
    # Open Source
    with tabs[2]:
        recommendations = analysis.get("opensource_recommendations", [])
        
        if not recommendations:
            st.info("No open source recommendations.")
        else:
            for repo in recommendations:
                project = repo.get("project_name", repo.get("repository", ""))
                
                if not project:
                    continue
                
                why_this_project = repo.get("why_this_project", repo.get("reason", ""))
                contribution_type = repo.get("contribution_type", "")
                career_impact = repo.get("career_impact", "")
                github_url = repo.get("github_url", "")
                
                st.markdown(f"""
### 🐙 {project}

**Why this project**
{why_this_project}

**Contribution idea**
{contribution_type}

**Career impact**
{career_impact}
""")
                
                if github_url:
                    st.markdown(f"**GitHub Repository:** [{github_url}]({github_url})")
                
                st.markdown("---")
    
    # Mentor
    with tabs[3]:
        st.info(analysis.get("mentor_summary", "No mentor advice available."))
    
    # =====================================================
    # CAREER ACTIONS
    # =====================================================
    
    st.divider()
    st.header("Career Actions")
    
    col1, col2 = st.columns(2)
    
    # Save Application
    with col1:
        if st.button("💼 Save Job Application", use_container_width=True):
            if not st.session_state.analysis:
                st.warning("Run analysis first.")
            else:
                analysis = st.session_state.analysis
                company = analysis.get("company_name", "Unknown Company")
                role = analysis.get("job_title", "Unknown Role")
                
                try:
                    saved = add_application(
                        company,
                        role,
                        st.session_state.job_description,
                        analysis.get("match_score", 0)
                    )
                    
                    if saved.get("status") == "duplicate":
                        st.warning(f"⚠️ {saved.get('message')}")
                    else:
                        st.success(f"""
                        ✅ **Application Saved Successfully!**
                        
                        **Company:** {company}
                        **Role:** {role}
                        **Status:** Applied
                        """)
                    
                    trigger_n8n(
                        "application_saved",
                        {
                            "company": company,
                            "role": role,
                            "job_description": st.session_state.job_description,
                            "user_email": st.session_state.get("user_email", ""),
                            "user_id": st.session_state.get("user_id", "")
                        }
                    )
                except Exception as e:
                    st.error(f"Application save failed: {e}")
    
    # Interview Practice - FIXED
    with col2:
        if st.button("🎤 Start Interview Practice", use_container_width=True):
            # FIX: Use st.navigation or just rerun with a flag
            # Option 1: Use query params to indicate navigation
            st.query_params["page"] = "interview"
            st.rerun()
    
    # Check if we need to navigate to interview page
    if st.query_params.get("page") == "interview":
        # Clear the query param to prevent loops
        st.query_params.clear()
        # Navigate to interview page using st.switch_page
        st.switch_page("pages/4_Interview_Practice.py")

