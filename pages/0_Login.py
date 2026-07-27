import os
import logging
import re

import streamlit as st

from dotenv import load_dotenv
from supabase import create_client, Client


# =====================================================
# ENVIRONMENT
# =====================================================

load_dotenv()


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

APP_URL = os.getenv(
    "APP_URL",
    "http://localhost:8501"
)


if not SUPABASE_URL:
    raise RuntimeError("Missing SUPABASE_URL")


if not SUPABASE_KEY:
    raise RuntimeError("Missing SUPABASE_KEY")



# =====================================================
# SUPABASE CLIENT
# =====================================================

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)



# =====================================================
# LOGGING
# =====================================================

logging.basicConfig(
    level=logging.INFO
)

logger = logging.getLogger(
    "CareerLensAuth"
)



# =====================================================
# VALIDATION
# =====================================================

def validate_email(email):

    if not email:
        return False


    email = email.strip().lower()


    pattern = r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$"


    return re.fullmatch(
        pattern,
        email
    ) is not None




# =====================================================
# SESSION MANAGEMENT
# =====================================================

def save_user_session(user):


    if not user:
        return



    email = getattr(
        user,
        "email",
        None
    )


    metadata = getattr(
        user,
        "user_metadata",
        {}
    )



    st.session_state["user"] = user


    st.session_state["user_id"] = getattr(
        user,
        "id",
        None
    )


    st.session_state["user_email"] = email


    st.session_state["user_name"] = metadata.get(
        "full_name",
        "Career User"
    )


    logger.info(
        f"Session saved for {email}"
    )






def restore_session():

    if "user" in st.session_state:

        return st.session_state["user"]


    return None





def get_user():

    return st.session_state.get(
        "user"
    )





def get_user_id():

    return st.session_state.get(
        "user_id"
    )





def get_user_email():

    return st.session_state.get(
        "user_email"
    )





def get_user_name():

    return st.session_state.get(
        "user_name",
        "Career User"
    )






# =====================================================
# LOGIN
# =====================================================

def login_email(
    email,
    password
):


    if not email or not password:

        return {

            "success": False,

            "error":
            "Email and password required."

        }



    email = email.strip().lower()



    if not validate_email(email):

        return {

            "success": False,

            "error":
            "Invalid email format."

        }



    try:


        response = supabase.auth.sign_in_with_password(

            {

                "email": email,

                "password": password

            }

        )



        user = response.user



        if not user:


            return {

                "success":False,

                "error":
                "Login failed."

            }



        save_user_session(
            user
        )



        return {


            "success":True,


            "user":user

        }




    except Exception as e:


        error = str(e)


        logger.error(
            f"Login error: {error}"
        )



        if "Invalid login credentials" in error:


            return {


                "success":False,


                "error":
                "Invalid email or password."

            }



        if "Email not confirmed" in error:


            return {


                "success":False,


                "error":
                "Please verify your email first."

            }



        return {


            "success":False,


            "error":
            error

        }






# =====================================================
# SIGNUP
# =====================================================


def signup_email(

    email,

    password,

    name

):


    if not email or not password or not name:


        return {


            "success":False,


            "error":
            "All fields are required."

        }



    email = email.strip().lower()



    if not validate_email(email):


        return {


            "success":False,


            "error":
            "Invalid email format."

        }




    if len(password) < 8:


        return {


            "success":False,


            "error":
            "Password must contain at least 8 characters."

        }




    try:


        response = supabase.auth.sign_up(


            {


                "email":email,


                "password":password,


                "options":{


                    "email_redirect_to":APP_URL,


                    "data":{


                        "full_name":
                        name.strip()

                    }

                }

            }

        )




        user = response.user




        return {


            "success":True,


            "user":user,


            "message":
            "Account created successfully. Please verify your email."

        }





    except Exception as e:


        logger.error(
            f"Signup error: {e}"
        )


        return {


            "success":False,


            "error":
            str(e)

        }







# =====================================================
# PASSWORD RESET
# =====================================================

def reset_password(email):


    if not email:


        return {


            "success":False,


            "error":
            "Email required."

        }




    try:


        supabase.auth.reset_password_for_email(

            email,


            {

                "redirect_to":
                f"{APP_URL}/reset_password"

            }

        )



        return {


            "success":True,


            "message":
            "Password reset email sent."

        }



    except Exception as e:


        return {


            "success":False,


            "error":
            str(e)

        }






# =====================================================
# EMAIL VERIFICATION CALLBACK
# =====================================================


def exchange_verification_code(code):


    try:


        response = supabase.auth.exchange_code_for_session(
            code
        )



        if response.user:


            save_user_session(
                response.user
            )


            return True



    except Exception as e:


        logger.error(
            f"Verification error: {e}"
        )



    return False







# =====================================================
# LOGOUT
# =====================================================


def logout():


    try:

        supabase.auth.sign_out()


    except Exception as e:

        logger.error(
            f"Logout error: {e}"
        )


    st.session_state.clear()
