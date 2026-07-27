import os
import logging
import requests
import streamlit as st

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


N8N_WEBHOOK_URL = os.getenv(
    "N8N_WEBHOOK_URL",
    ""
)


# =====================================================
# LOGGING
# =====================================================

logging.basicConfig(
    level=logging.INFO
)

logger = logging.getLogger(
    "CareerLensAI"
)


# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="CareerLens AI",
    page_icon="🚀",
    layout="wide"
)



# =====================================================
# GLOBAL STYLE WITH ANIMATIONS
# =====================================================

st.markdown(
"""
<style>

/* Base styles */
.stApp {
    background:#070B14;
    color:#E2E8F0;
}

h1,h2,h3,h4 {
    color:#F8FAFC;
}

p,label {
    color:#CBD5E1;
}

.card {
    background:#111827;
    border:1px solid #1E293B;
    border-radius:18px;
    padding:22px;
    margin-bottom:18px;
    animation: fadeInUp 0.6s ease-out;
}

.stButton button {
    background:#03045E !important;
    color:white !important;
    border-radius:12px !important;
    height:45px;
    font-weight:600;
    transition: all 0.3s ease !important;
}

.stButton button:hover {
    background:#023E8A !important;
    transform: scale(1.05) !important;
    box-shadow: 0 0 20px rgba(3, 4, 94, 0.5) !important;
}

textarea, input {
    background:#111827 !important;
    color:white !important;
    transition: all 0.3s ease !important;
}

textarea:focus, input:focus {
    border-color: #03045E !important;
    box-shadow: 0 0 15px rgba(3, 4, 94, 0.3) !important;
    transform: scale(1.01) !important;
}

/* Animations */
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

@keyframes fadeInDown {
    from {
        opacity: 0;
        transform: translateY(-30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes fadeInLeft {
    from {
        opacity: 0;
        transform: translateX(-30px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

@keyframes fadeInRight {
    from {
        opacity: 0;
        transform: translateX(30px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

@keyframes shimmer {
    0% {
        background-position: -1000px 0;
    }
    100% {
        background-position: 1000px 0;
    }
}

@keyframes float {
    0% {
        transform: translateY(0px);
    }
    50% {
        transform: translateY(-10px);
    }
    100% {
        transform: translateY(0px);
    }
}

@keyframes glow {
    0% {
        box-shadow: 0 0 5px rgba(3, 4, 94, 0.2);
    }
    50% {
        box-shadow: 0 0 20px rgba(3, 4, 94, 0.6);
    }
    100% {
        box-shadow: 0 0 5px rgba(3, 4, 94, 0.2);
    }
}

/* Animated header */
.header-animation {
    animation: fadeInDown 0.8s ease-out;
}

/* Metric cards animation */
.metric-card {
    animation: fadeInUp 0.6s ease-out;
    transition: all 0.3s ease;
}

.metric-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 30px rgba(3, 4, 94, 0.3);
}

/* Tab animations */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    animation: fadeIn 0.5s ease-out;
}

.stTabs [data-baseweb="tab"] {
    transition: all 0.3s ease;
}

.stTabs [data-baseweb="tab"]:hover {
    transform: translateY(-2px);
}

/* Success and info messages animation */
.stAlert {
    animation: fadeInUp 0.5s ease-out;
}

/* Progress bar animation */
.stProgress > div > div {
    animation: shimmer 2s infinite linear;
    background: linear-gradient(90deg, #03045E 0%, #023E8A 50%, #03045E 100%);
    background-size: 1000px 100%;
}

/* Spinner animation */
.stSpinner {
    animation: shimmer 1.5s ease-in-out infinite;
}

/* Divider animation */
hr {
    animation: fadeIn 0.5s ease-out;
}

@keyframes fadeIn {
    from {
        opacity: 0;
    }
    to {
        opacity: 1;
    }
}

/* Card hover effects */
.card:hover {
    border-color: #03045E;
    box-shadow: 0 0 30px rgba(3, 4, 94, 0.2);
    transition: all 0.3s ease;
}

/* Expandable sections */
.streamlit-expanderHeader {
    transition: all 0.3s ease;
}

.streamlit-expanderHeader:hover {
    background: #1a2332 !important;
}

/* Columns animation */
[data-testid="column"] {
    animation: fadeInUp 0.7s ease-out;
}

/* Success message animation */
.stSuccess {
    animation: glow 2s ease-in-out infinite;
}

/* Info box animation */
.stInfo {
    animation: fadeInLeft 0.6s ease-out;
}

/* Warning box animation */
.stWarning {
    animation: fadeInRight 0.6s ease-out;
}

/* Error box animation */
.stError {
    animation: fadeIn 0.5s ease-out;
}

/* Floating animation for icons */
.fa, .emoji {
    animation: float 3s ease-in-out infinite;
}

/* Button loading animation */
.stButton button:disabled {
    animation: shimmer 1.5s infinite linear;
    background: linear-gradient(90deg, #03045E 0%, #023E8A 50%, #03045E 100%);
    background-size: 200% 100%;
}

/* Metric value animation */
[data-testid="stMetricValue"] {
    animation: fadeInUp 0.8s ease-out;
    transition: all 0.3s ease;
}

[data-testid="stMetricValue"]:hover {
    transform: scale(1.05);
    color: #06B6D4;
}

/* Tooltip animation */
[data-testid="stTooltipContent"] {
    animation: fadeIn 0.3s ease-out;
}

/* Checkbox animation */
.stCheckbox label {
    transition: all 0.3s ease;
}

.stCheckbox label:hover {
    transform: scale(1.02);
}

/* Radio button animation */
.stRadio label {
    transition: all 0.3s ease;
}

.stRadio label:hover {
    transform: scale(1.02);
}

/* Selectbox animation */
.stSelectbox > div {
    transition: all 0.3s ease;
}

.stSelectbox > div:hover {
    transform: scale(1.02);
}

/* Multiselect animation */
.stMultiSelect > div {
    transition: all 0.3s ease;
}

.stMultiSelect > div:hover {
    transform: scale(1.02);
}

/* Slider animation */
.stSlider > div {
    transition: all 0.3s ease;
}

.stSlider > div:hover {
    transform: scale(1.02);
}

/* Image animation */
.stImage img {
    animation: fadeIn 0.8s ease-out;
    transition: all 0.3s ease;
}

.stImage img:hover {
    transform: scale(1.02);
}

/* Dataframe animation */
.dataframe {
    animation: fadeInUp 0.6s ease-out;
}

/* Plotly chart container animation */
[data-testid="stPlotlyChart"] {
    animation: fadeInUp 0.7s ease-out;
    transition: all 0.3s ease;
}

[data-testid="stPlotlyChart"]:hover {
    transform: scale(1.01);
    box-shadow: 0 10px 30px rgba(3, 4, 94, 0.2);
}

/* Professional Success Popup */
.success-popup {
    background: linear-gradient(135deg, #0f172a, #1e293b);
    border: 1px solid #10b981;
    border-radius: 16px;
    padding: 28px 32px;
    margin: 20px 0;
    animation: fadeInUp 0.6s ease-out;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.success-popup .icon {
    font-size: 48px;
    text-align: center;
    margin-bottom: 8px;
}

.success-popup h3 {
    color: #10b981;
    text-align: center;
    margin: 8px 0;
    font-size: 22px;
}

.success-popup .subtitle {
    color: #94a3b8;
    text-align: center;
    font-size: 14px;
    margin-bottom: 16px;
}

.success-popup .details {
    background: #0f172a;
    border-radius: 10px;
    padding: 14px 18px;
    margin: 12px 0;
}

.success-popup .details p {
    color: #cbd5e1;
    font-size: 14px;
    margin: 4px 0;
}

.success-popup .details .label {
    color: #64748b;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.success-popup .checklist {
    margin: 12px 0;
}

.success-popup .checklist-item {
    color: #94a3b8;
    font-size: 13px;
    padding: 4px 0;
    display: flex;
    align-items: center;
    gap: 8px;
}

.success-popup .checklist-item .check {
    color: #10b981;
    font-size: 16px;
}

.success-popup .footer-note {
    color: #64748b;
    font-size: 12px;
    text-align: center;
    margin-top: 12px;
    border-top: 1px solid #1e293b;
    padding-top: 12px;
}

</style>
""",
unsafe_allow_html=True
)



# =====================================================
# N8N EVENT HELPER
# =====================================================

def trigger_n8n(
    event,
    data=None
):

    if not N8N_WEBHOOK_URL:

        return False


    payload = {

        "event": event,

        **(data or {})

    }



    try:

        response = requests.post(

            N8N_WEBHOOK_URL,

            json=payload,

            timeout=10

        )


        return response.status_code in [
            200,
            201,
            202
        ]



    except Exception as e:

        logger.warning(
            f"n8n trigger failed: {e}"
        )

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



for key,value in DEFAULT_STATE.items():

    if key not in st.session_state:

        st.session_state[key] = value




# =====================================================
# HEADER WITH ANIMATION
# =====================================================

st.markdown(
"""
<div class="card header-animation">

<h1>
🚀 CareerLens AI
</h1>


<p>
AI Resume Matching • GitHub Intelligence • Career Roadmap
</p>


</div>
""",
unsafe_allow_html=True
)




# =====================================================
# INPUT SECTION
# =====================================================

st.header(
"Candidate Profile"
)



col1,col2 = st.columns(2)



with col1:

    uploaded_file = st.file_uploader(

        "Upload Resume PDF",

        type=[
            "pdf"
        ]

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

        resume_text = extract_text_from_pdf(
            uploaded_file
        )


        st.success(
            "Resume extracted successfully"
        )


    except Exception as e:


        st.error(
            f"Resume extraction failed: {e}"
        )




# =====================================================
# ANALYSIS FUNCTION
# =====================================================


def run_analysis():


    if not resume_text:


        st.warning(
            "Please upload resume first."
        )

        return



    if not job_description.strip():


        st.warning(
            "Please enter job description."
        )

        return



    github_data = None



    if github_url:


        username = (

            github_url

            .rstrip("/")

            .split("/")[-1]

        )


        with st.spinner(

            "Analyzing GitHub profile..."

        ):


            github_data = analyze_github(
                username
            )



    with st.spinner(

        "Generating AI career report..."

    ):


        result = analyze_resume(

            resume_text,

            job_description,

            github_data

        )


    # Debug: Print the result to see what's being returned
    logger.info(f"Analysis result: {result}")


    if result.get("error"):
        
        # Check if it's a quota error
        if result.get("quota_error") or "quota" in str(result.get("error", "")).lower():
            st.error(
                "⚠️ **AI Service Unavailable**\n\n"
                "The analysis service has reached its daily limit. Please try again later."
            )
        else:
            st.error(
                f"❌ {result.get('error')}"
            )
        
        return




    st.session_state.analysis = result

    st.session_state.resume_text = resume_text

    st.session_state.job_description = job_description

    st.session_state.github_data = github_data



    trigger_n8n(

        "career_analysis_completed",

        {

            "company":

            result.get(
                "company_name",
                ""
            ),


            "match_score":

            result.get(
                "match_score",
                0
            )

        }

    )



    st.success(
        "Career analysis completed 🚀"
    )




# =====================================================
# RUN BUTTON
# =====================================================


if st.button(

    "Analyze Career Profile 🚀",

    use_container_width=True

):

    run_analysis()
    # =====================================================
# REPORT SECTION
# =====================================================

if st.session_state.analysis:


    analysis = st.session_state.analysis


    st.divider()


    st.header(
        "Career Readiness Report"
    )



    # =================================================
    # METRICS
    # =================================================


    c1,c2,c3 = st.columns(3)



    with c1:

        st.metric(

            "Job Match",

            f"{analysis.get('match_score',0)}%"

        )



    with c2:

        st.metric(

            "GitHub Score",

            f"{analysis.get('github_review',{}).get('score',0)}/100"

        )



    with c3:

        st.metric(

            "Candidate Level",

            analysis.get(
                "candidate_level",
                "N/A"
            )

        )




    st.divider()



    tabs = st.tabs(

        [

            "📌 Skills Analysis",

            "🐙 GitHub Review",

            "🌎 Open Source",

            "🧭 Career Mentor"

        ]

    )



    # =================================================
    # SKILLS ANALYSIS - UPDATED WITH FIX
    # =================================================


    with tabs[0]:


        requirements = analysis.get(

            "requirement_analysis",

            []

        )



        if not requirements:

            st.info(
                "No skill analysis available."
            )

        else:

            for item in requirements:

                skill = item.get(
                    "skill",
                    "Skill"
                )

                status = item.get(
                    "status",
                    ""
                )

                if status == "strong_match":
                    icon = "🟢"
                elif status == "partial_match":
                    icon = "🟡"
                else:
                    icon = "🔴"

                st.markdown(
                    f"""
### {icon} {skill}

**Status:** {status.replace("_"," ").title()}

**Evidence**
{item.get("evidence","")}
"""
                )

                if status != "strong_match":
                    missing = item.get(
                        "missing",
                        ""
                    )
                    next_step = item.get(
                        "next_step",
                        ""
                    )

                    if missing:
                        st.markdown(
                            f"""
**Missing:**
{missing}
"""
                        )

                    if next_step:
                        st.markdown(
                            f"""
**Next Step:**
{next_step}
"""
                        )




    # =================================================
    # GITHUB REVIEW
    # =================================================


    with tabs[1]:


        github = analysis.get(

            "github_review",

            {}

        )


        st.subheader(

            f"GitHub Score: {github.get('score',0)}/100"

        )



        col1,col2 = st.columns(2)



        with col1:


            st.write(
                "### Strengths"
            )


            strengths = github.get(

                "strengths",

                []

            )


            if strengths:


                for item in strengths:

                    st.success(item)


            else:

                st.info(
                    "No strengths found."
                )





        with col2:


            st.write(
                "### Improvement Areas"
            )


            weaknesses = github.get(

                "weaknesses",

                []

            )


            if weaknesses:


                for item in weaknesses:

                    st.warning(item)


            else:

                st.info(
                    "No weaknesses found."
                )






    # =================================================
    # OPEN SOURCE - FIXED FRONTEND
    # =================================================


    with tabs[2]:


        recommendations = analysis.get(

            "opensource_recommendations",

            []

        )



        if not recommendations:

            st.info(
                "No open source recommendations."
            )

        else:

            for repo in recommendations:

                # Try to get project_name, fallback to repository for backwards compatibility
                project = repo.get(
                    "project_name",
                    ""
                )

                # If project_name is empty, try repository field
                if not project:
                    project = repo.get(
                        "repository",
                        ""
                    )

                # If still empty, skip this entry
                if not project:
                    continue

                # Get other fields with fallbacks
                why_this_project = repo.get(
                    "why_this_project",
                    repo.get("reason", "")
                )

                contribution_type = repo.get(
                    "contribution_type",
                    ""
                )

                career_impact = repo.get(
                    "career_impact",
                    ""
                )

                github_url = repo.get(
                    "github_url",
                    ""
                )

                st.markdown(
                    f"""
### 🐙 {project}


**Why this project**

{why_this_project}


**Contribution idea**

{contribution_type}


**Career impact**

{career_impact}
"""
                )

                if github_url:
                    st.markdown(
                        f"""
**GitHub Repository**
[{github_url}]({github_url})
"""
                    )

                st.markdown("---")






    # =================================================
    # MENTOR
    # =================================================


    with tabs[3]:


        st.info(

            analysis.get(

                "mentor_summary",

                "No mentor advice available."

            )

        )






# =====================================================
# CAREER ACTIONS
# =====================================================


st.divider()


st.header(

    "Career Actions"

)



col1,col2 = st.columns(2)





# =====================================================
# SAVE APPLICATION - WITH PROFESSIONAL POPUP
# =====================================================


with col1:


    if st.button(

        "💼 Save Job Application",

        use_container_width=True

    ):



        if not st.session_state.analysis:


            st.warning(

                "Run analysis first."

            )



        else:


            analysis = st.session_state.analysis



            company = analysis.get(

                "company_name",

                "Unknown Company"

            )



            role = analysis.get(

                "job_title",

                "Unknown Role"

            )



            try:


                saved = add_application(

                    company,

                    role,

                    st.session_state.job_description,

                    analysis.get(

                        "match_score",

                        0

                    )

                )


                # Check if duplicate
                if saved.get("status") == "duplicate":
                    st.warning(
                        f"⚠️ {saved.get('message')}"
                    )
                else:
                    # Professional Success Popup - Using triple quotes properly
                    success_html = f"""
                    <div class="success-popup">
                        <div class="icon">✅</div>
                        <h3>Application Saved Successfully</h3>
                        <div class="subtitle">Your application has been submitted and is being processed</div>
                        
                        <div class="details">
                            <p><span class="label">Company</span><br>{company}</p>
                            <p><span class="label">Role</span><br>{role}</p>
                            <p><span class="label">Status</span><br><span style="color: #10b981;">Applied</span></p>
                        </div>
                        
                        <div class="checklist">
                            <div class="checklist-item">
                                <span class="check">✓</span> Application recorded in your dashboard
                            </div>
                            <div class="checklist-item">
                                <span class="check">✓</span> AI analysis saved for future reference
                            </div>
                            <div class="checklist-item">
                                <span class="check">✉</span> Confirmation email sent to your inbox
                            </div>
                        </div>
                        
                        <div class="footer-note">
                            📧 Please check your email inbox (and spam folder) for the confirmation.
                        </div>
                    </div>
                    """
                    
                    st.markdown(success_html, unsafe_allow_html=True)



                trigger_n8n(

                    "application_saved",

                    {

                        "company": company,

                        "role": role,

                        "job_description": st.session_state.job_description,

                        "user_email": st.session_state.get(
                            "user_email",
                            ""
                        ),

                        "user_id": st.session_state.get(
                            "user_id",
                            ""
                        )

                    }

                )



            except Exception as e:


                st.error(

                    f"Application save failed: {e}"

                )







# =====================================================
# INTERVIEW PRACTICE
# =====================================================


with col2:


    if st.button(

        "🎤 Start Interview Practice",

        use_container_width=True

    ):


        st.switch_page(

            "pages/4_Interview_Practice.py"
     
        )
