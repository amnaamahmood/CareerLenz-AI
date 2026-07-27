import os
import logging
import re
import requests
import httpx

import streamlit as st

from dotenv import load_dotenv
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions

# =====================================================
# ENVIRONMENT
# =====================================================

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
APP_URL = os.getenv("APP_URL", "http://localhost:8501")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")

if not SUPABASE_URL:
    raise RuntimeError("Missing SUPABASE_URL")
if not SUPABASE_KEY:
    raise RuntimeError("Missing SUPABASE_KEY")

# FIX: Configure Supabase with 30 second timeout
supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY,
    options=ClientOptions(
        httpx_client=httpx.Client(timeout=30.0)  # 30 second timeout
    )
)

# =====================================================
# LOGGING
# =====================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CareerLensAuth")

# =====================================================
# HELPERS
# =====================================================

def validate_email(email):
    if not email:
        return False
    email = email.strip().lower()
    pattern = r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$"
    return re.fullmatch(pattern, email) is not None

def trigger_n8n(event, data=None):
    if not N8N_WEBHOOK_URL:
        return False
    payload = {"event": event, **(data or {})}
    try:
        response = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=10)
        return response.status_code in [200, 201, 202]
    except Exception as e:
        logger.error(f"N8N error: {e}")
        return False

# =====================================================
# SESSION MANAGEMENT
# =====================================================

def save_user_session(user):
    if not user:
        return
    email = getattr(user, 'email', None)
    if not email:
        user_metadata = getattr(user, 'user_metadata', {})
        email = user_metadata.get('email')
    if not email:
        if hasattr(user, '_data'):
            email = user._data.get('email')
    if not email:
        logger.warning(f"No email found for user: {user.id if hasattr(user, 'id') else 'unknown'}")
        email = "user@example.com"
    
    st.session_state.user = user
    st.session_state.user_id = getattr(user, 'id', None)
    st.session_state.user_email = email
    user_metadata = getattr(user, 'user_metadata', {})
    st.session_state.user_name = user_metadata.get('full_name', 'Career User')
    logger.info(f"User session saved: {email}")

def restore_session():
    return st.session_state.get("user")

def get_user():
    return st.session_state.get("user")

def get_user_id():
    return st.session_state.get("user_id")

def get_user_email():
    return st.session_state.get("user_email")

def get_user_name():
    return st.session_state.get("user_name", "Career User")

# =====================================================
# SIGNUP - FIXED WITH TIMEOUT HANDLING
# =====================================================

def signup_email(email, password, name):
    if not email or not password or not name:
        return {"success": False, "error": "All fields required."}
    
    email = email.strip().lower()
    if not validate_email(email):
        return {"success": False, "error": "Invalid email."}
    
    if len(password) < 8:
        return {"success": False, "error": "Password must contain 8 characters."}
    
    try:
        response = supabase.auth.sign_up(
            {
                "email": email,
                "password": password,
                "options": {
                    "email_redirect_to": APP_URL,
                    "data": {"full_name": name.strip()}
                }
            }
        )
        
        logger.info(f"Signup successful for {email}")
        
        if response.user and hasattr(response.user, 'confirmed_at') and response.user.confirmed_at is None:
            return {
                "success": True,
                "user": response.user,
                "requires_confirmation": True,
                "message": "Verification email sent. Please check your inbox and spam folder."
            }
        
        trigger_n8n("user_signup", {"email": email, "name": name.strip()})
        
        return {"success": True, "user": response.user}
    
    except httpx.ReadTimeout:
        logger.error(f"Signup timed out for {email}")
        return {
            "success": False,
            "error": "Request timed out. Your account may still have been created. Try logging in."
        }
    except Exception as e:
        error = str(e)
        logger.error(f"Signup error: {error}")
        if "already registered" in error.lower() or "user already" in error.lower():
            return {
                "success": False,
                "error": "An account with this email already exists. Please log in instead."
            }
        return {"success": False, "error": error}

# =====================================================
# LOGIN - FIXED WITH TIMEOUT HANDLING
# =====================================================

def login_email(email, password):
    if not email or not password:
        return {"success": False, "error": "Email and password required."}
    
    email = email.strip().lower()
    if not validate_email(email):
        return {"success": False, "error": "Invalid email format."}
    
    try:
        response = supabase.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
        
        user = response.user
        if not user:
            return {"success": False, "error": "Login failed."}
        
        save_user_session(user)
        trigger_n8n("user_login", {"user_id": user.id, "email": user.email})
        
        return {"success": True, "user": user}
    
    except httpx.ReadTimeout:
        return {"success": False, "error": "Login timed out. Please try again."}
    except Exception as e:
        error = str(e)
        logger.error(f"Login error: {error}")
        if "Email not confirmed" in error:
            return {"success": False, "error": "Please verify your email first."}
        if "Invalid login credentials" in error:
            return {"success": False, "error": "Invalid email or password."}
        return {"success": False, "error": error}

# =====================================================
# PASSWORD RESET - FIXED WITH TIMEOUT HANDLING
# =====================================================

def reset_password(email):
    if not email:
        return {"success": False, "error": "Email required."}
    
    email = email.strip().lower()
    
    try:
        supabase.auth.reset_password_for_email(
            email,
            {"redirect_to": f"{APP_URL}/reset_password"}
        )
        logger.info(f"Password reset email sent to {email}")
        return {
            "success": True,
            "message": "Password reset email sent. Please check your inbox and spam folder."
        }
    
    except httpx.ReadTimeout:
        return {"success": False, "error": "Password reset timed out. Please try again."}
    except Exception as e:
        error = str(e)
        logger.error(f"Password reset error: {error}")
        return {"success": False, "error": error}

# =====================================================
# VERIFICATION
# =====================================================

def exchange_verification_code(code):
    try:
        response = supabase.auth.exchange_code_for_session(code)
        if response.user:
            save_user_session(response.user)
            return True
    except Exception as e:
        logger.error(f"Verification failed {e}")
    return False

# =====================================================
# LOGOUT
# =====================================================

def logout():
    try:
        supabase.auth.sign_out()
    except Exception as e:
        logger.error(f"Logout error {e}")
    st.session_state.clear()
