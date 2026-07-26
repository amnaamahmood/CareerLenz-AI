import os
import streamlit as st

from dotenv import load_dotenv

from auth import (
    get_user,
    restore_session,
    logout
)

from database import supabase


# =====================================
# ENVIRONMENT
# =====================================

load_dotenv()


APP_NAME = os.getenv(
    "APP_NAME",
    "CareerLens AI"
)


# =====================================
# PAGE CONFIG
# =====================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)



# =====================================
# EMAIL VERIFICATION HANDLER
# =====================================

def handle_email_verification():

    try:

        query_params = st.query_params


        if "code" not in query_params:

            return



        verification_code = query_params["code"]



        response = (
            supabase
            .auth
            .exchange_code_for_session(
                verification_code
            )
        )



        if response.session:


            st.session_state.user = response.user

            st.session_state.user_id = response.user.id

            st.session_state.user_email = response.user.email



            st.success(
                "Email verified successfully 🚀"
            )


            st.query_params.clear()


            st.rerun()



    except Exception as e:


        st.error(
            f"Email verification failed: {str(e)}"
        )





handle_email_verification()





# =====================================
# GLOBAL THEME
# =====================================

st.markdown(
"""
<style>


.stApp {

background:#070B14 !important;

}



html,body,[class*="css"]{

font-family:Inter,sans-serif;

}



h1,h2,h3,h4,h5,h6{

color:#F8FAFC !important;

}



p,label{

color:#CBD5E1 !important;

}



/* SIDEBAR */

[data-testid="stSidebar"]{

background:#0B1120 !important;

}



[data-testid="stSidebarNav"] li{

border-radius:10px;

margin-bottom:5px;

}



[data-testid="stSidebarNav"] li:hover{

background:#03045E !important;

}



/* BRAND */


.brand-title{

color:#F8FAFC;

font-size:25px;

font-weight:800;

}



.brand-subtitle{

color:#94A3B8;

font-size:13px;

}



/* USER CARD */


.bottom-bar{

position:sticky;

bottom:0;

background:#0B1120;

padding-top:12px;

}



.user-card{

background:#111827;

border:1px solid #1E293B;

border-radius:14px;

padding:14px;

display:flex;

align-items:center;

gap:12px;

}



.avatar{

height:40px;

width:40px;

background:#03045E;

border-radius:50%;

display:flex;

justify-content:center;

align-items:center;

font-size:20px;

}



.user-name{

color:#F8FAFC;

font-size:14px;

font-weight:700;

}



.user-email{

color:#94A3B8;

font-size:12px;

}



/* BUTTON */


.stButton button{

background:#03045E !important;

color:white !important;

border-radius:10px !important;

border:none !important;

}



.stButton button:hover{

background:#030268 !important;

}



</style>

""",
unsafe_allow_html=True
)





# =====================================
# SESSION RESTORE
# =====================================

restore_session()

user = get_user()





# =====================================
# LOGIN ROUTE
# =====================================

if not user:


    login_page = st.Page(

        "pages/0_Login.py",

        title="Login",

        icon="🔐"

    )


    pg = st.navigation(

        {

            "Authentication":

            [

                login_page

            ]

        }

    )


    pg.run()


    st.stop()





# =====================================
# APPLICATION PAGES
# =====================================


home = st.Page(

    "pages/1_Home.py",

    title="Home",

    icon="🏠"

)



career_analysis = st.Page(

    "pages/2_Career_Analysis.py",

    title="Career Analysis",

    icon="📊"

)



dashboard = st.Page(

    "pages/3_Dashboard.py",

    title="Dashboard",

    icon="📈"

)



interview = st.Page(

    "pages/4_Interview_Practice.py",

    title="Interview Practice",

    icon="🎤"

)



applications = st.Page(

    "pages/5_Applications.py",

    title="Applications",

    icon="💼"

)





pg = st.navigation(

{

"CareerLens AI":

[

home,

career_analysis,

dashboard,

interview,

applications

]

}

)





# =====================================
# SIDEBAR
# =====================================


with st.sidebar:


    st.markdown(

        """
        <div class="brand-title">
        🚀 CareerLens AI
        </div>

        <div class="brand-subtitle">
        Your AI Career Copilot
        </div>
        """,

        unsafe_allow_html=True

    )


    st.divider()



    username = "Career User"



    metadata = getattr(
        user,
        "user_metadata",
        {}
    )



    username = (

        metadata.get(
            "full_name"
        )

        or

        metadata.get(
            "name"
        )

        or

        "Career User"

    )



    st.markdown(

        '<div class="bottom-bar">',

        unsafe_allow_html=True

    )



    st.markdown(

        f"""

        <div class="user-card">

        <div class="avatar">
        👤
        </div>


        <div>

        <div class="user-name">
        {username}
        </div>


        <div class="user-email">
        {user.email}
        </div>


        </div>

        </div>

        """,

        unsafe_allow_html=True

    )



    st.write("")



    if st.button(

        "🚪 Logout",

        use_container_width=True

    ):


        logout()

        st.rerun()



    st.markdown(

        "</div>",

        unsafe_allow_html=True

    )





# =====================================
# RUN
# =====================================

pg.run()