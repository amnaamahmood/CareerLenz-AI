import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv

# =====================================================
# ENVIRONMENT
# =====================================================

load_dotenv()

# Get API key from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Interview Practice",
    page_icon="🎤",
    layout="wide"
)

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
</style>
""",
    unsafe_allow_html=True
)

# =====================================================
# GET ANALYSIS DATA - WITH SAFE CHECK
# =====================================================

# FIX: Safely get analysis from session state
analysis = st.session_state.get("analysis")

# If analysis is None or empty, redirect back or show error
if not analysis:
    st.error("❌ No career analysis found. Please complete the analysis first.")
    
    # Button to go back to main page
    if st.button("Go to Career Analysis", use_container_width=True):
        st.switch_page("app.py")
    
    st.stop()  # Stop execution if no analysis

# =====================================================
# EXTRACT DATA SAFELY WITH FALLBACKS
# =====================================================

# FIX: Use .get() with fallback values for all fields
company = analysis.get("company_name", "the company")
role = analysis.get("job_title", "this role")
job_description = st.session_state.get("job_description", "")

# Get skills from analysis - handle different possible structures
skills_data = analysis.get("requirement_analysis", [])
skills = []
if skills_data:
    # Extract skill names from requirement_analysis
    for item in skills_data:
        if isinstance(item, dict):
            skill_name = item.get("skill", "")
            if skill_name:
                skills.append(skill_name)

# If no skills found, use a default list
if not skills:
    skills = ["Technical skills", "Communication", "Problem solving", "Team collaboration"]

# =====================================================
# HEADER
# =====================================================

st.markdown(
    f"""
<div class="card">
    <h1>🎤 Interview Practice</h1>
    <p>Prepare for your interview at <strong>{company}</strong> for the <strong>{role}</strong> position</p>
</div>
""",
    unsafe_allow_html=True
)

# Show job description if available
if job_description:
    with st.expander("📋 View Job Description"):
        st.write(job_description)

# =====================================================
# INTERVIEW CONFIGURATION
# =====================================================

st.subheader("Interview Settings")

col1, col2 = st.columns(2)

with col1:
    question_count = st.selectbox(
        "Number of Questions",
        options=[3, 5, 8, 10],
        index=0
    )

with col2:
    difficulty = st.selectbox(
        "Difficulty Level",
        options=["Easy", "Medium", "Hard"],
        index=0
    )

# =====================================================
# SKILLS DISPLAY
# =====================================================

st.write("### Skills to Focus On")
skills_cols = st.columns(4)
for idx, skill in enumerate(skills[:4]):  # Show first 4 skills
    with skills_cols[idx % 4]:
        st.info(f"📌 {skill}")

# =====================================================
# START INTERVIEW BUTTON
# =====================================================

def generate_interview_questions(company, role, skills, job_desc, count, difficulty):
    """Generate interview questions using Gemini API"""
    
    if not GEMINI_API_KEY:
        return None, "Gemini API key not configured."
    
    # Prepare prompt
    skills_text = ", ".join(skills[:5])
    
    prompt = f"""
    You are an expert interview coach. Generate {count} {difficulty.lower()} interview questions for a candidate interviewing for the position of {role} at {company}.
    
    Job Description: {job_desc[:500] if job_desc else "Not provided"}
    
    Key Skills: {skills_text}
    
    For each question:
    1. Start with a brief context
    2. Ask a specific, relevant question
    3. Provide a short tip on what the interviewer is looking for
    
    Format your response as a JSON array with objects containing:
    - "question": The question text
    - "context": Brief context
    - "tip": What the interviewer is looking for
    - "difficulty": The difficulty level
    
    Example format:
    [
        {{
            "question": "Tell me about a time you faced a challenging technical problem",
            "context": "Behavioral question about problem-solving",
            "tip": "Use the STAR method to structure your answer",
            "difficulty": "Medium"
        }}
    ]
    """
    
    try:
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        
        response = requests.post(
            f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Extract the text from the response
            text = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "[]")
            
            # Clean and parse JSON
            # Remove markdown code blocks if present
            text = text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            
            questions = json.loads(text)
            return questions, None
        else:
            return None, f"API Error: {response.status_code}"
            
    except json.JSONDecodeError as e:
        return None, f"Error parsing response: {e}"
    except Exception as e:
        return None, f"Error: {e}"

# =====================================================
# SESSION STATE FOR INTERVIEW
# =====================================================

if "interview_questions" not in st.session_state:
    st.session_state.interview_questions = []
if "current_question_index" not in st.session_state:
    st.session_state.current_question_index = 0
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "interview_started" not in st.session_state:
    st.session_state.interview_started = False
if "interview_complete" not in st.session_state:
    st.session_state.interview_complete = False

# =====================================================
# START INTERVIEW
# =====================================================

if st.button("🎤 Start Interview", use_container_width=True):
    with st.spinner("Generating interview questions..."):
        questions, error = generate_interview_questions(
            company, role, skills, job_description, question_count, difficulty
        )
        
        if questions:
            st.session_state.interview_questions = questions
            st.session_state.current_question_index = 0
            st.session_state.answers = {}
            st.session_state.interview_started = True
            st.session_state.interview_complete = False
            st.rerun()
        else:
            st.error(f"❌ Failed to generate questions: {error}")

# =====================================================
# INTERVIEW PROGRESS
# =====================================================

if st.session_state.interview_started and not st.session_state.interview_complete:
    questions = st.session_state.interview_questions
    current_idx = st.session_state.current_question_index
    
    if not questions:
        st.warning("No questions generated. Please start the interview again.")
        if st.button("Restart Interview", use_container_width=True):
            st.session_state.interview_started = False
            st.rerun()
    else:
        # Progress bar
        progress = (current_idx + 1) / len(questions)
        st.progress(progress)
        st.write(f"Question {current_idx + 1} of {len(questions)}")
        
        # Display current question
        question_data = questions[current_idx]
        
        with st.container():
            st.markdown(
                f"""
                <div class="card">
                    <h3>Question {current_idx + 1}</h3>
                    <p style="font-size: 18px; color: #E2E8F0;">{question_data.get('question', '')}</p>
                    <p style="font-size: 14px; color: #64748B;">
                        💡 <strong>Context:</strong> {question_data.get('context', '')}
                    </p>
                    <details>
                        <summary style="color: #06B6D4; cursor: pointer;">Show Tip</summary>
                        <p style="color: #94A3B8; margin-top: 8px;">{question_data.get('tip', '')}</p>
                    </details>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Answer input
            answer = st.text_area(
                "Your Answer",
                height=150,
                placeholder="Type your answer here...",
                key=f"answer_{current_idx}"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("⏭️ Next Question", use_container_width=True):
                    # Save answer
                    st.session_state.answers[current_idx] = answer
                    
                    if current_idx + 1 < len(questions):
                        st.session_state.current_question_index = current_idx + 1
                        st.rerun()
                    else:
                        st.session_state.interview_complete = True
                        st.rerun()
            
            with col2:
                if st.button("🔄 Skip Question", use_container_width=True):
                    st.session_state.answers[current_idx] = "Skipped"
                    if current_idx + 1 < len(questions):
                        st.session_state.current_question_index = current_idx + 1
                        st.rerun()
                    else:
                        st.session_state.interview_complete = True
                        st.rerun()

# =====================================================
# INTERVIEW COMPLETE
# =====================================================

if st.session_state.interview_complete:
    st.markdown(
        """
        <div class="card" style="border-color: #10B981;">
            <h2 style="text-align: center; color: #10B981;">🎉 Interview Complete!</h2>
            <p style="text-align: center; color: #94A3B8;">You've completed all questions. Here's a summary:</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Show summary of answers
    for idx, q_data in enumerate(st.session_state.interview_questions):
        with st.expander(f"Question {idx + 1}: {q_data.get('question', '')[:80]}..."):
            st.write("**Question:**")
            st.write(q_data.get('question', ''))
            st.write("**Your Answer:**")
            answer = st.session_state.answers.get(idx, "Not answered")
            st.write(answer)
    
    # Feedback and action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Retry Interview", use_container_width=True):
            st.session_state.interview_started = False
            st.session_state.interview_complete = False
            st.session_state.interview_questions = []
            st.rerun()
    
    with col2:
        if st.button("📊 Get Feedback", use_container_width=True):
            st.info("Feedback feature coming soon!")
    
    with col3:
        if st.button("🏠 Return Home", use_container_width=True):
            st.switch_page("app.py")
