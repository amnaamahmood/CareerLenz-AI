import os
import logging
import re
import requests

import streamlit as st

from dotenv import load_dotenv
from supabase import create_client, Client



# =====================================================
# ENVIRONMENT
# =====================================================

load_dotenv()



SUPABASE_URL = os.getenv(
    "SUPABASE_URL"
)


SUPABASE_KEY = os.getenv(
    "SUPABASE_KEY"
)


APP_URL = os.getenv(
    "APP_URL",
    "http://localhost:8501"
)


N8N_WEBHOOK_URL = os.getenv(
    "N8N_WEBHOOK_URL"
)




if not SUPABASE_URL:

    raise RuntimeError(
        "Missing SUPABASE_URL"
    )


if not SUPABASE_KEY:

    raise RuntimeError(
        "Missing SUPABASE_KEY"
    )





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
# HELPERS
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





def trigger_n8n(

    event,

    data=None

):


    if not N8N_WEBHOOK_URL:

        return False



    payload = {


        "event":
        event,


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


        logger.error(
            f"N8N error: {e}"
        )


        return False





# =====================================================
# SESSION MANAGEMENT
# =====================================================


def save_user_session(user):


    if not user:

        return



    st.session_state.user = user

    st.session_state.user_id = user.id

    st.session_state.user_email = user.email





def restore_session():

    # Only restore from current session state, not from Supabase
    if "user" in st.session_state:
        return st.session_state.user

    return None





def get_user():


    return st.session_state.get(
        "user"
    )





def get_user_id():


    return st.session_state.get(
        "user_id"
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

            "success":False,

            "error":
            "Email and password required."

        }


    email = email.strip().lower()

    if not validate_email(email):


        return {

            "success":False,

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



        user=response.user



        if not user:


            return {

                "success":False,

                "error":
                "Login failed."

            }




        save_user_session(
            user
        )



        trigger_n8n(

            "user_login",

            {

                "user_id":
                user.id,


                "email":
                user.email

            }

        )




        return {


            "success":
            True,


            "user":
            user

        }





    except Exception as e:



        error=str(e)
        
        # Log the full error for debugging
        logger.error(f"Login error details: {error}")



        if "Email not confirmed" in error:


            return {


                "success":False,


                "error":
                "Please verify your email first."

            }


        if "Invalid login credentials" in error:
            
            return {

                "success": False,
                
                "error": "Invalid email or password. Please check your credentials."

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
            "All fields required."

        }


    email = email.strip().lower()

    if not validate_email(email):


        return {

            "success":False,

            "error":
            "Invalid email."

        }



    if len(password)<8:


        return {


            "success":False,


            "error":
            "Password must contain 8 characters."

        }




    try:



        response=supabase.auth.sign_up(

            {

                "email": email,

                "password": password,

                "options":

                {

                    "email_redirect_to":
                    APP_URL,


                    "data":

                    {

                        "full_name":
                        name.strip()

                    }

                }

            }

        )


        # Log success
        logger.info(f"Signup successful for {email}")
        
        # Check if user needs email confirmation
        if response.user and hasattr(response.user, 'confirmed_at') and response.user.confirmed_at is None:
            return {

                "success": True,
                
                "user": response.user,
                
                "requires_confirmation": True,
                
                "message": "Verification email sent. Please check your inbox and spam folder."

            }




        trigger_n8n(

            "user_signup",

            {

                "email": email,

                "name": name.strip()

            }

        )





        return {


            "success":
            True,


            "user":
            response.user


        }





    except Exception as e:


        error = str(e)
        logger.error(f"Signup error: {error}")
        
        return {


            "success":
            False,


            "error":
            error

        }






# =====================================================
# PASSWORD RESET
# =====================================================


def reset_password(

    email

):


    if not email:


        return {

            "success":False,

            "error":
            "Email required."

        }


    email = email.strip().lower()

    try:



        response = supabase.auth.reset_password_for_email(

            email,

            {

                "redirect_to":
                f"{APP_URL}/reset_password"

            }

        )


        logger.info(f"Password reset email sent to {email}")


        return {


            "success":
            True,
            
            "message": "Password reset email sent. Please check your inbox and spam folder."

        }




    except Exception as e:


        error = str(e)
        logger.error(f"Password reset error: {error}")
        
        return {


            "success":
            False,


            "error":
            error

        }







# =====================================================
# VERIFICATION
# =====================================================


def exchange_verification_code(

    code

):


    try:



        response=supabase.auth.exchange_code_for_session(

            code

        )



        if response.user:


            save_user_session(

                response.user

            )


            return True



    except Exception as e:


        logger.error(
            f"Verification failed {e}"
        )



    return False







# =====================================================
# LOGOUT - UPDATED WITH CLEAR
# =====================================================


def logout():


    try:

        supabase.auth.sign_out()


    except Exception as e:


        logger.error(
            f"Logout error {e}"
        )


    # Clear all session state
    st.session_state.clear()
