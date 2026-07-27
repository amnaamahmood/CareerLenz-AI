import streamlit as st
import streamlit.components.v1 as components

from auth import (
    get_user,
    restore_session,
    login_email,
    signup_email,
    logout
)


# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="CareerLens AI",
    page_icon="🚀",
    layout="centered"
)


# =====================================================
# DISABLE BROWSER AUTOFILL / AUTOCOMPLETE (ALL FIELDS)
# =====================================================
# Chrome ignores autocomplete="off" on login/signup-style fields.
# It heuristically decides a field is "email"/"username"/"password"
# based on name/id/type/nearby label text, and once it decides
# that, it shows saved suggestions (saved emails, GitHub username,
# saved passwords) regardless of autocomplete="off".
#
# This targets EVERY <input> on the page (both the Login tab and
# the Create Account tab — Name, Email, Password, Confirm Password)
# and:
#   1. Assigns a random, non-standard autocomplete token instead of
#      "off" (Chrome doesn't recognize it, so it disables
#      suggestions entirely instead of falling back to a guess).
#   2. Uses autocomplete="new-password" specifically for password
#      fields (tells Chrome this is a new credential, not one to
#      suggest from the saved list).
#   3. Randomizes name/id so Chrome's field-matching heuristic can't
#      key off them.
#   4. Adds data-lpignore / data-1p-ignore / data-form-type for
#      LastPass / 1Password / Dashlane.
#   5. Re-runs on every DOM mutation (Streamlit reruns/tab switches)
#      via MutationObserver, but skips fields already patched so
#      typing isn't disrupted.

components.html(
    """
    <script>
    function randomToken() {
        return 'no-autofill-' + Math.random().toString(36).slice(2);
    }

    function disableAutofill() {
        const inputs = window.parent.document.querySelectorAll('input, textarea');
        inputs.forEach((el) => {
            if (el.dataset.autofillPatched) return;

            const isPassword = el.type === 'password';

            el.setAttribute('autocomplete', isPassword ? 'new-password' : randomToken());
            el.setAttribute('autocorrect', 'off');
            el.setAttribute('autocapitalize', 'off');
            el.setAttribute('spellcheck', 'false');

            el.setAttribute('name', randomToken());
            if (el.id) el.setAttribute('id', randomToken());

            el.setAttribute('data-lpignore', 'true');
            el.setAttribute('data-1p-ignore', 'true');
            el.setAttribute('data-form-type', 'other');
            el.setAttribute('readonly', 'true');
            setTimeout(() => el.removeAttribute('readonly'), 100);

            el.dataset.autofillPatched = 'true';
        });
    }

    disableAutofill();
    const observer = new MutationObserver(disableAutofill);
    observer.observe(window.parent.document.body, { childList: true, subtree: true });
    </script>
    """,
    height=0,
)


# =====================================================
# GLOBAL STYLE
# =====================================================

st.markdown(
"""
<style>

html, body, [data-testid="stAppViewContainer"]{

min-height:100vh !important;

}

.stApp{

background:
radial-gradient(
circle at top,
#172554,
#020617 70%
);

min-height:100vh !important;

}


.block-container{

max-width:850px !important;
padding-top:2rem !important;
min-height:100vh !important;

}


/* HERO */

.hero{

text-align:center;
margin-bottom:30px;

}


.hero h1{

font-size:52px;
font-weight:900;
color:white;

}


.hero span{

color:#2563EB;

}


.hero p{

color:#94A3B8;
font-size:18px;

}



/* CARD */

.card{

background:#0F172A;

border:1px solid #1E293B;

border-radius:20px;

padding:30px;

}



/* FEATURES */


.feature{

background:#111827;

border:1px solid #1E293B;

border-radius:16px;

height:120px;

padding:18px;

text-align:center;

}



.feature h3{

color:#60A5FA;

font-size:18px;

}



.feature p{

color:#94A3B8;

font-size:13px;

}



/* INPUT */


input,
textarea{

background:#020617 !important;

color:white !important;

}



label{

color:#CBD5E1 !important;

}



/* BUTTON */


.stButton{

width:100% !important;

}



.stButton button{


height:48px !important;

width:100% !important;


background:#03045E !important;

color:white !important;


border-radius:12px !important;

border:none !important;


font-weight:700;


}



.stButton button:hover{

background:#023E8A !important;

}


.message-slot{

min-height:56px;

}


</style>

""",
unsafe_allow_html=True
)



# =====================================================
# SESSION RESTORE
# =====================================================

restore_session()

user = get_user()



# =====================================================
# EXISTING USER
# =====================================================

if user:


    st.markdown(
    """
    <div class="card">

    <h2 style="text-align:center;color:#2563EB">

    Welcome Back 👋

    </h2>

    </div>
    """,
    unsafe_allow_html=True
    )


    st.write("")


    st.info(
        user.email
    )



    if st.button(
        "🚀 Open Dashboard",
        key="dashboard_btn"
    ):

        st.switch_page(
            "pages/3_Dashboard.py"
        )



    if st.button(
        "🚪 Logout",
        key="logout_btn"
    ):

        if "user" in st.session_state:
            del st.session_state["user"]
        
        logout()

        st.rerun()



    st.stop()



# =====================================================
# HERO
# =====================================================


st.markdown(
"""
<div class="hero">

<h1>
🚀 Career<span>Lens</span> AI
</h1>


<p>
Your intelligent AI career copilot
<br>
Resume Intelligence • Job Matching • Interview AI
</p>


</div>

""",
unsafe_allow_html=True
)




# =====================================================
# FEATURES
# =====================================================


c1,c2,c3 = st.columns(3)


features = [

    ("📄 Resume AI",
     "AI resume analysis"),

    ("🎯 Job Match",
     "Skill gap detection"),

    ("🎤 Interview AI",
     "AI interview practice")

]



for col,(title,text) in zip(
    [c1,c2,c3],
    features
):

    with col:

        st.markdown(

        f"""

        <div class="feature">

        <h3>{title}</h3>

        <p>{text}</p>

        </div>

        """,

        unsafe_allow_html=True

        )



st.write("")



# =====================================================
# AUTH TABS
# =====================================================


login_tab, signup_tab = st.tabs(
[
"🔐 Login",
"🚀 Create Account"
]
)



# =====================================================
# LOGIN
# =====================================================


with login_tab:


    st.markdown(
    '<div class="card">',
    unsafe_allow_html=True
    )


    st.subheader(
        "Welcome Back"
    )


    login_email_input = st.text_input(
        "Email",
        key="login_email"
    )


    login_password = st.text_input(
        "Password",
        type="password",
        key="login_password"
    )


    login_message_slot = st.container()


    if st.button(
        "Login",
        key="login_submit"
    ):


        with login_message_slot:

            if not login_email_input or not login_password:
                st.error("Please enter both email and password.")
            else:
                result = login_email(

                    login_email_input,

                    login_password

                )



                if result["success"]:

                    st.session_state["user"] = result["user"]

                    st.success(
                        "Login successful 🚀"
                    )

                    st.rerun()



                else:


                    st.error(
                        result["error"]
                    )



    st.markdown(
    "</div>",
    unsafe_allow_html=True
    )





# =====================================================
# SIGNUP
# =====================================================


with signup_tab:


    st.markdown(
    '<div class="card">',
    unsafe_allow_html=True
    )



    st.subheader(
        "Create CareerLens Account"
    )



    signup_name = st.text_input(

        "Full Name",

        key="signup_name"

    )


    signup_email_input = st.text_input(

        "Email",

        key="signup_email"

    )



    signup_password = st.text_input(

        "Password",

        type="password",

        key="signup_password"

    )



    signup_confirm = st.text_input(

        "Confirm Password",

        type="password",

        key="signup_confirm"

    )


    signup_message_slot = st.container()


    if st.button(

        "Create Account",

        key="signup_submit"

    ):


        with signup_message_slot:

            if not signup_name.strip():

                st.error(
                    "Name is required."
                )
                
            elif not signup_email_input.strip():
                
                st.error(
                    "Email is required."
                )

            elif signup_password != signup_confirm:


                st.error(
                    "Passwords do not match."
                )



            elif len(signup_password) < 8:


                st.error(
                    "Password must contain at least 8 characters."
                )



            else:


                result = signup_email(

                    signup_email_input,

                    signup_password,

                    signup_name

                )



                if result["success"]:
                    
                    st.success(
                        "Account created successfully! You can now login."
                    )


                else:


                    st.error(
                        result["error"]
                    )



    st.markdown(
    "</div>",
    unsafe_allow_html=True
    )
