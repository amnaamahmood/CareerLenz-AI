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
# GLOBAL STYLE
# =====================================================

st.markdown(
"""
<style>

/* FIX: lock the page + main container to a stable minimum height so
   content appearing/disappearing (errors, success messages, etc.)
   does not visibly shrink/expand the page on every button click */

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


/* POPUP OVERLAY */

.popup-overlay {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.7);
    z-index: 9999;
    justify-content: center;
    align-items: center;
    backdrop-filter: blur(5px);
}

.popup-overlay.active {
    display: flex;
}

.popup-box {
    background: #0F172A;
    border: 2px solid #F59E0B;
    border-radius: 20px;
    padding: 30px 40px;
    max-width: 500px;
    width: 90%;
    box-shadow: 0 0 50px rgba(245, 158, 11, 0.3);
    animation: popIn 0.3s ease-out;
    text-align: center;
}

@keyframes popIn {
    0% { transform: scale(0.8); opacity: 0; }
    100% { transform: scale(1); opacity: 1; }
}

.popup-box h3 {
    color: #F59E0B;
    font-size: 24px;
    margin-top: 0;
    margin-bottom: 12px;
}

.popup-box p {
    color: #CBD5E1;
    font-size: 15px;
    line-height: 1.6;
    margin-bottom: 20px;
}

.popup-close-btn {
    background: #F59E0B;
    color: #0F172A;
    border: none;
    padding: 10px 30px;
    border-radius: 10px;
    font-weight: 700;
    font-size: 16px;
    cursor: pointer;
    transition: all 0.2s;
}

.popup-close-btn:hover {
    background: #D97706;
    transform: scale(1.05);
}

/* FIX: reserve a stable slot for feedback messages so the page
   doesn't jump in height when an error/success message appears */

.message-slot{

min-height:56px;

}

</style>

""",
unsafe_allow_html=True
)


# =====================================================
# JAVASCRIPT FOR POPUP
# =====================================================

popup_js = """
<script>
(function() {
    // Wait for the DOM to be fully loaded
    function waitForElement(selector, callback) {
        if (document.querySelector(selector)) {
            callback(document.querySelector(selector));
            return;
        }
        const observer = new MutationObserver(function(mutations) {
            if (document.querySelector(selector)) {
                observer.disconnect();
                callback(document.querySelector(selector));
            }
        });
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    // Function to show popup
    function showPopup() {
        const overlay = document.getElementById('email-popup-overlay');
        if (overlay) {
            overlay.classList.add('active');
        }
    }

    // Function to hide popup
    function hidePopup() {
        const overlay = document.getElementById('email-popup-overlay');
        if (overlay) {
            overlay.classList.remove('active');
        }
    }

    // Wait for the email input field
    waitForElement('input[data-testid="baseWebInput"][aria-label="Email"]', function(emailInput) {
        let hasShownPopup = false;
        
        // Add blur event listener (triggers when user clicks away from email field)
        emailInput.addEventListener('blur', function() {
            const emailValue = this.value.trim();
            // Only show popup if email is not empty and hasn't been shown yet
            if (emailValue.length > 0 && !hasShownPopup) {
                showPopup();
                hasShownPopup = true;
            }
        });

        // Also show popup when Enter key is pressed in the email field
        emailInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                const emailValue = this.value.trim();
                if (emailValue.length > 0 && !hasShownPopup) {
                    showPopup();
                    hasShownPopup = true;
                }
            }
        });

        // Close popup when clicking the close button
        const closeBtn = document.getElementById('popup-close-btn');
        if (closeBtn) {
            closeBtn.addEventListener('click', hidePopup);
        }

        // Close popup when clicking outside the popup box
        const overlay = document.getElementById('email-popup-overlay');
        if (overlay) {
            overlay.addEventListener('click', function(e) {
                if (e.target === this) {
                    hidePopup();
                }
            });
        }
    });
})();
</script>
"""


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

        # Clear user from session state first
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


    # FIX: fixed-height slot for the feedback message so the layout
    # doesn't jump when it appears/disappears
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

                    # Fix: Use dictionary syntax for session state
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


    # FIX: fixed-height slot for the feedback message so the layout
    # doesn't jump when it appears/disappears
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
                    
                    # Simplified success message
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



# =====================================================
# POPUP HTML (shows when user finishes typing email)
# =====================================================

st.markdown(
"""
<!-- POPUP OVERLAY -->
<div id="email-popup-overlay" class="popup-overlay">
    <div class="popup-box">
        <h3>⚠️ Important Notice</h3>
        <p>
            Please use a <strong>real, active email address</strong> — not a random or temporary one.<br><br>
            Your account confirmation and job application updates are sent to this inbox, and a fake email may prevent you from accessing your account later.
        </p>
        <button id="popup-close-btn" class="popup-close-btn">I Understand ✓</button>
    </div>
</div>
""",
unsafe_allow_html=True
)


# =====================================================
# INJECT JAVASCRIPT
# =====================================================

components.html(popup_js, height=0, scrolling=False)
