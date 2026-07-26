import os
import logging
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from dotenv import load_dotenv

from dashboard_manager import (
    get_career_analysis,
    get_application_data,
    get_interview_data,
    get_profile
)


# =====================================================
# ENVIRONMENT
# =====================================================

load_dotenv()


APP_NAME = os.getenv(
    "APP_NAME",
    "CareerLens AI"
)


logging.basicConfig(
    level=logging.INFO
)

logger = logging.getLogger(
    "CareerLensDashboard"
)




# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title=f"{APP_NAME} Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)




# =====================================================
# PREMIUM DASHBOARD THEME
# =====================================================

st.markdown(
"""
<style>

html, body, [class*="css"] {

    font-family: "Inter", sans-serif;

}



.stApp {

    background:
    radial-gradient(
        circle at top left,
        #111827,
        #070B14 45%
    );

    color:white;

}



h1,h2,h3,h4 {

    color:#F8FAFC !important;

}



p,span,label {

    color:#CBD5E1;

}



.block-container {

    padding-top:2rem;

}




/* KPI CARDS */


.kpi-card {

    padding:22px;

    border-radius:22px;

    color:white;

    height:130px;

    box-shadow:
    0 15px 35px rgba(0,0,0,.25);

}



.kpi-purple {

    background:
    linear-gradient(
        135deg,
        #7C3AED,
        #4F46E5
    );

}



.kpi-cyan {

    background:
    linear-gradient(
        135deg,
        #0891B2,
        #06B6D4
    );

}



.kpi-pink {

    background:
    linear-gradient(
        135deg,
        #DB2777,
        #9333EA
    );

}



.kpi-green {

    background:
    linear-gradient(
        135deg,
        #059669,
        #10B981
    );

}



.kpi-title {

    font-size:14px;

    opacity:.8;

}



.kpi-value {

    font-size:35px;

    font-weight:800;

    margin-top:8px;

}




/* CARDS */


.dashboard-card {


    background:

    rgba(17,24,39,.75);


    backdrop-filter:

    blur(12px);


    border:

    1px solid rgba(255,255,255,.08);


    border-radius:22px;


    padding:20px;


}





/* SIDEBAR */


[data-testid="stSidebar"] {

    background:#080D18;

}





/* BUTTON */


.stButton button {


    background:

    linear-gradient(
        135deg,
        #03045E,
        #023E8A
    ) !important;


    color:white !important;


    border-radius:12px !important;


    border:none !important;


    font-weight:700;


}





[data-testid="stMetric"] {

    background:transparent;

}


</style>

""",
unsafe_allow_html=True
)





# =====================================================
# HEADER
# =====================================================


st.markdown(
f"""
<h1>
📊 {APP_NAME} Dashboard
</h1>

<p style="
font-size:18px;
color:#94A3B8;
">
Track your AI career progress, applications,
interviews and technical growth.
</p>

""",
unsafe_allow_html=True
)


st.divider()






# =====================================================
# LOAD USER DATA SAFELY
# =====================================================


def safe_load(function):

    try:

        data = function()

        return data if data else []


    except Exception as e:

        logger.error(
            f"Dashboard loading error: {e}"
        )

        return []




career_data = safe_load(
    get_career_analysis
)


applications = safe_load(
    get_application_data
)


interviews = safe_load(
    get_interview_data
)


try:

    profile = get_profile()

except Exception:

    profile = {}






# =====================================================
# CALCULATIONS
# =====================================================


total_apps = len(
    applications
)



avg_match = 0


if career_data:


    avg_match = (

        sum(

            float(
                item.get(
                    "match_score",
                    0
                )
                or 0
            )

            for item in career_data

        )

        /
        len(career_data)

    )




avg_github = 0


if career_data:


    avg_github = (

        sum(

            float(

                item.get(
                    "github_score",
                    0
                )

                or 0

            )

            for item in career_data

        )

        /
        len(career_data)

    )





avg_interview = 0


if interviews:


    avg_interview = (

        sum(

            float(

                item.get(
                    "score",
                    0
                )

                or 0

            )

            for item in interviews

        )

        /
        len(interviews)

    )







# =====================================================
# KPI SECTION
# =====================================================


c1,c2,c3,c4 = st.columns(4)



with c1:

    st.markdown(
    f"""
    <div class="kpi-card kpi-purple">

    <div class="kpi-title">
    Applications
    </div>

    <div class="kpi-value">
    {total_apps}
    </div>

    </div>
    """,
    unsafe_allow_html=True
    )




with c2:

    st.markdown(
    f"""
    <div class="kpi-card kpi-cyan">

    <div class="kpi-title">
    Average Job Match
    </div>

    <div class="kpi-value">
    {avg_match:.0f}%
    </div>

    </div>
    """,
    unsafe_allow_html=True
    )




with c3:

    st.markdown(
    f"""
    <div class="kpi-card kpi-pink">

    <div class="kpi-title">
    Interview Score
    </div>

    <div class="kpi-value">
    {avg_interview:.0f}%
    </div>

    </div>
    """,
    unsafe_allow_html=True
    )




with c4:

    st.markdown(
    f"""
    <div class="kpi-card kpi-green">

    <div class="kpi-title">
    GitHub Score
    </div>

    <div class="kpi-value">
    {avg_github:.0f}
    </div>

    </div>
    """,
    unsafe_allow_html=True
    )



st.write("")




# =====================================================
# APPLICATION ANALYTICS
# =====================================================


st.divider()


st.markdown(
"""
<h2>
💼 Application Analytics
</h2>
""",
unsafe_allow_html=True
)



if applications:


    df_apps = pd.DataFrame(
        applications
    )



    if "status" in df_apps.columns:


        status_data = (

            df_apps["status"]

            .value_counts()

            .reset_index()

        )


        status_data.columns = [

            "Status",
            "Count"

        ]



        col1,col2 = st.columns(
            [1,1]
        )



        with col1:


            fig = go.Figure(

                data=[

                    go.Pie(

                        labels=status_data["Status"],

                        values=status_data["Count"],

                        hole=.65,

                        textinfo="label+percent"

                    )

                ]

            )


            fig.update_layout(

                title="Application Status",

                template="plotly_dark",

                height=350,

                paper_bgcolor="rgba(0,0,0,0)",

                plot_bgcolor="rgba(0,0,0,0)"

            )


            st.plotly_chart(

                fig,

                use_container_width=True

            )


        with col2:


            fig = px.bar(

                status_data,

                x="Status",

                y="Count",

                text="Count",

                title="Application Funnel",

                color="Status"

            )


            fig.update_layout(

                template="plotly_dark",

                height=350,

                paper_bgcolor="rgba(0,0,0,0)",

                plot_bgcolor="rgba(0,0,0,0)"

            )


            st.plotly_chart(

                fig,

                use_container_width=True

            )


else:


    st.info(
        "No applications saved yet."
    )







# =====================================================
# CAREER GROWTH GRAPH
# =====================================================


st.divider()


st.markdown(
"""
<h2>
📈 Career Growth
</h2>
""",
unsafe_allow_html=True
)




if career_data:


    df = pd.DataFrame(
        career_data
    )



    if "created_at" in df.columns and "match_score" in df.columns:


        df["created_at"] = pd.to_datetime(

            df["created_at"],

            errors="coerce"

        )


        df = df.dropna(
            subset=["created_at"]
        )



        fig = go.Figure()



        fig.add_trace(

            go.Scatter(

                x=df["created_at"],

                y=df["match_score"],

                mode="lines+markers",

                name="Job Match",

                line=dict(

                    color="#06B6D4",

                    width=4

                ),

                fill="tozeroy",

                fillcolor="rgba(6,182,212,0.15)"

            )

        )



        fig.update_layout(

            title="AI Career Readiness Progress",

            template="plotly_dark",

            height=400,

            paper_bgcolor="rgba(0,0,0,0)",

            plot_bgcolor="rgba(0,0,0,0)",

            hovermode="x unified"

        )


        st.plotly_chart(

            fig,

            use_container_width=True

        )


    else:


        st.info(
            "Career history data unavailable."
        )



else:


    st.info(
        "Complete career analysis to generate growth tracking."
    )








# =====================================================
# INTERVIEW PERFORMANCE
# =====================================================


st.divider()


st.markdown(
"""
<h2>
🎤 Interview Performance
</h2>
""",
unsafe_allow_html=True
)




if interviews:


    df_inter = pd.DataFrame(
        interviews
    )



    if (
        "created_at" in df_inter.columns
        and
        "score" in df_inter.columns
    ):


        df_inter["created_at"] = pd.to_datetime(

            df_inter["created_at"],

            errors="coerce"

        )



        df_inter = df_inter.dropna(

            subset=[
                "created_at"
            ]

        )




        fig = go.Figure()



        fig.add_trace(

            go.Scatter(

                x=df_inter["created_at"],

                y=df_inter["score"],

                mode="lines+markers",

                name="Interview Score",

                line=dict(

                    color="#EC4899",

                    width=4

                ),

                fill="tozeroy",

                fillcolor="rgba(236,72,153,0.15)"

            )

        )



        fig.update_layout(

            title="Interview Score History",

            template="plotly_dark",

            height=380,

            paper_bgcolor="rgba(0,0,0,0)",

            plot_bgcolor="rgba(0,0,0,0)"

        )



        st.plotly_chart(

            fig,

            use_container_width=True

        )


else:


    st.info(
        "No interview sessions yet."
    )








# =====================================================
# SKILL GAP INTELLIGENCE
# =====================================================


st.divider()


st.markdown(
"""
<h2>
🧠 Skill Gap Intelligence
</h2>
""",
unsafe_allow_html=True
)



missing_skills = []



for item in career_data:


    skills = item.get(

        "missing_skills",

        []

    )



    if isinstance(
        skills,
        list
    ):


        for skill in skills:


            if isinstance(
                skill,
                dict
            ):


                value = skill.get(

                    "requirement",

                    ""

                )


            else:


                value = skill



            if value:

                missing_skills.append(
                    value
                )




if missing_skills:


    skill_df = pd.DataFrame(

        {

            "Skill":
            missing_skills

        }

    )



    counts = (

        skill_df

        .value_counts()

        .reset_index()

    )



    counts.columns = [

        "Skill",

        "Count"

    ]




    fig = px.bar(

        counts,

        x="Count",

        y="Skill",

        orientation="h",

        title="Most Required Missing Skills",

        color="Count"

    )



    fig.update_layout(

        template="plotly_dark",

        height=450,

        paper_bgcolor="rgba(0,0,0,0)",

        plot_bgcolor="rgba(0,0,0,0)"

    )



    st.plotly_chart(

        fig,

        use_container_width=True

    )


else:


    st.info(
        "No skill gaps detected."
    )








# =====================================================
# RECENT ACTIVITY
# =====================================================


st.divider()


st.markdown(
"""
<h2>
🕒 Recent Activity
</h2>
""",
unsafe_allow_html=True
)




if applications:


    for item in applications[:5]:


        st.markdown(

        f"""

        <div class="dashboard-card">


        📌 Applied for


        <b>
        {item.get(
            'role',
            'Role'
        )}
        </b>


        at


        <b>
        {item.get(
            'company',
            'Company'
        )}
        </b>


        <br>


        Status:

        {item.get(
            'status',
            'Applied'
        )}


        </div>


        <br>


        """,

        unsafe_allow_html=True

        )


else:


    st.info(
        "No recent activity."
    )








# =====================================================
# PROFILE SUMMARY
# =====================================================


st.divider()


st.markdown(
"""
<h2>
👤 Profile
</h2>
""",
unsafe_allow_html=True
)



if profile:


    st.markdown(

    f"""

    <div class="dashboard-card">


    <h3>
    {profile.get(
        "name",
        "CareerLens User"
    )}
    </h3>


    <p>

    Email:

    {profile.get(
        "email",
        "Not available"
    )}

    </p>


    </div>


    """,

    unsafe_allow_html=True

    )


else:


    st.info(
        "Profile information unavailable."
    )








# =====================================================
# FOOTER
# =====================================================


st.divider()



st.caption(

    f"{APP_NAME} • AI Powered Career Intelligence Platform"

)