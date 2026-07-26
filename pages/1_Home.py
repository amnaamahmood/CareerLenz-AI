import os
import streamlit as st

from dotenv import load_dotenv


# ===================================== #
# ENVIRONMENT
# ===================================== #

load_dotenv()


APP_NAME = os.getenv(
    "APP_NAME",
    "CareerLens AI"
)

APP_DESCRIPTION = os.getenv(
    "APP_DESCRIPTION",
    "Your AI Career Copilot"
)


# ===================================== #
# PAGE CONFIG
# ===================================== #

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🚀",
    layout="wide"
)



# ===================================== #
# CSS
# ===================================== #

st.markdown(
"""
<style>

.stApp{
    background: radial-gradient(
        circle at top left,
        #111827,
        #070B14 55%
    );
    color:white;
}


h1,h2,h3{
    color:#F8FAFC !important;
}


p{
    color:#CBD5E1;
    font-size:16px;
}


/* HERO */

.hero-card{

    background:linear-gradient(
        135deg,
        rgba(30,41,59,.9),
        rgba(15,23,42,.9)
    );

    padding:35px 25px;

    border-radius:24px;

    border:1px solid #334155;

    text-align:center;

}



.logo-container{

    display:flex;

    align-items:center;

    justify-content:center;

    gap:15px;

    margin-bottom:10px;

}



.hero-rocket{

    font-size:52px;

}



.hero-title{

    font-size:55px;

    font-weight:900;

    color:#38BDF8;

}



.hero-subtitle{

    font-size:25px;

    font-weight:700;

    color:white;

    margin-top:5px;

}



/* STATS */

.stats-card{

    background:#111827;

    padding:18px;

    border-radius:18px;

    border:1px solid #1E293B;

    text-align:center;

    height:150px;

}



.stats-icon{

    font-size:35px;

}



.stats-title{

    font-size:20px;

    font-weight:800;

    color:white;

    margin-top:8px;

}



.stats-desc{

    font-size:14px;

    color:#94A3B8;

}



/* FEATURES */

.feature-card{

    background:#111827;

    padding:22px;

    border-radius:20px;

    border:1px solid #1E293B;

    min-height:210px;

}



.feature-icon{

    font-size:35px;

}



.feature-title{

    font-size:21px;

    font-weight:800;

    color:white;

    margin-top:10px;

}



.feature-desc{

    font-size:14px;

    color:#CBD5E1;

    line-height:1.5;

}



/* STEPS */


.step-card{

    background:#111827;

    padding:14px 18px;

    border-radius:15px;

    border-left:4px solid #38BDF8;

    margin-bottom:8px;

}



.step-title{

    font-size:18px;

    font-weight:800;

    color:white;

}



.step-desc{

    font-size:14px;

    color:#CBD5E1;

}



/* BUTTON */


.stButton button{

    background:linear-gradient(
        135deg,
        #03045E,
        #023E8A
    )!important;

    color:white!important;

    border-radius:12px!important;

    height:50px;

    font-weight:700;

    font-size:16px;

}



</style>

""",
unsafe_allow_html=True
)



# ===================================== #
# HERO
# ===================================== #

st.markdown(
f"""
<div class="hero-card">

<div class="logo-container">

<span class="hero-rocket">
🚀
</span>

<span class="hero-title">
{APP_NAME}
</span>

</div>


<div class="hero-subtitle">
{APP_DESCRIPTION}
</div>


<br>


<p>
Transform your career journey with AI-powered resume analysis,
GitHub intelligence, interview preparation and application tracking.
</p>


</div>
""",
unsafe_allow_html=True
)



st.write("")



# ===================================== #
# STATS
# ===================================== #

st.subheader(
"✨ Why CareerLens AI?"
)


cols = st.columns(4)


stats=[

(
"🤖",
"AI Powered",
"Career Intelligence"
),

(
"📄",
"Resume AI",
"Smart Matching"
),

(
"🐙",
"GitHub AI",
"Portfolio Review"
),

(
"🎤",
"AI Coach",
"Interview Practice"
)

]



for col,data in zip(cols,stats):

    with col:

        st.markdown(
        f"""
        <div class="stats-card">

        <div class="stats-icon">
        {data[0]}
        </div>


        <div class="stats-title">
        {data[1]}
        </div>


        <div class="stats-desc">
        {data[2]}
        </div>


        </div>
        """,
        unsafe_allow_html=True
        )



st.divider()



# ===================================== #
# FEATURES
# ===================================== #

st.subheader(
"🚀 Everything You Need For Career Growth"
)



cols = st.columns(3)



features=[

(
"📄",
"AI Resume Matching",
"Compare your resume with job descriptions and discover your career readiness score."
),

(
"🐙",
"GitHub Intelligence",
"Analyze repositories and get portfolio improvement suggestions."
),

(
"🎤",
"AI Interview Coach",
"Practice realistic interviews and receive AI feedback."
)

]



for col,item in zip(cols,features):

    with col:

        st.markdown(
        f"""
        <div class="feature-card">


        <div class="feature-icon">
        {item[0]}
        </div>


        <div class="feature-title">
        {item[1]}
        </div>


        <div class="feature-desc">
        {item[2]}
        </div>


        </div>
        """,
        unsafe_allow_html=True
        )



st.divider()



# ===================================== #
# HOW IT WORKS
# ===================================== #

st.subheader(
"⚡ How CareerLens AI Works"
)



steps=[

(
"1️⃣ Upload Resume",
"Extract skills, experience and projects automatically."
),

(
"2️⃣ Add Job Description",
"Compare your profile with target role requirements."
),

(
"3️⃣ Career Analysis",
"Get match score, skill gaps and recommendations."
),

(
"4️⃣ Improve Profile",
"Upgrade GitHub, skills and portfolio."
),

(
"5️⃣ Prepare & Track",
"Practice interviews and manage applications."
)

]



for title,desc in steps:

    st.markdown(
    f"""
    <div class="step-card">

    <div class="step-title">
    {title}
    </div>


    <div class="step-desc">
    {desc}
    </div>


    </div>
    """,
    unsafe_allow_html=True
    )



st.divider()



# ===================================== #
# CTA
# ===================================== #

st.markdown(
"""
<div class="hero-card">

<h2>
🚀 Ready to Accelerate Your Career?
</h2>


<p>
✨ Let AI help you become job-ready faster.
</p>


<p style="font-size:14px;color:#94A3B8">

🎯 Analyze • Improve • Practice • Get Hired

</p>


</div>
""",
unsafe_allow_html=True
)



st.write("")



# ===================================== #
# NAVIGATION
# ===================================== #

c1,c2,c3 = st.columns(
[1,2,1]
)



with c2:


    if st.button(

        "🚀 Start Career Analysis",

        use_container_width=True,

        key="start_analysis_button"

    ):


        st.switch_page(
            "pages/2_Career_Analysis.py"
        )



st.divider()



st.caption(
f"🚀 {APP_NAME} • AI Powered Career Intelligence Platform"
)