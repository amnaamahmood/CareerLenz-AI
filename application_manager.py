# =====================================================
# application_manager.py
# CareerLens Application Management Module
# Production + Supabase + n8n Automation Ready
# =====================================================

import os
import time
import logging
import requests
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any

import streamlit as st

from dotenv import load_dotenv
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
import httpx

# =====================================================
# ENVIRONMENT CONFIGURATION
# =====================================================

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")
N8N_TIMEOUT = int(os.getenv("N8N_TIMEOUT", "10"))
N8N_RETRIES = int(os.getenv("N8N_RETRIES", "3"))
APP_NAME = os.getenv("APP_NAME", "CareerLens")
APP_ENV = os.getenv("APP_ENV", "development")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Missing Supabase environment variables.")

# =====================================================
# SUPABASE CLIENT WITH TIMEOUT
# =====================================================

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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("CareerLens-Applications")

# =====================================================
# SESSION STATE HELPERS
# =====================================================

def get_user_id() -> Optional[str]:
    """Get current user ID from session state."""
    # First try stored user_id
    user_id = st.session_state.get("user_id")
    if user_id:
        return user_id
    
    # Fallback to user object
    user = st.session_state.get("user")
    if user:
        user_id = getattr(user, 'id', None)
        if user_id:
            st.session_state["user_id"] = user_id
            return user_id
    
    return None

def get_user_email() -> Optional[str]:
    """Get current user email from session state."""
    # First try stored user_email
    user_email = st.session_state.get("user_email")
    if user_email:
        return user_email
    
    # Fallback to user object
    user = st.session_state.get("user")
    if user:
        user_email = getattr(user, 'email', None)
        if not user_email:
            user_metadata = getattr(user, 'user_metadata', {})
            user_email = user_metadata.get('email')
        if user_email:
            st.session_state["user_email"] = user_email
            return user_email
    
    return None

def get_user_name() -> str:
    """Get current user name from session state."""
    user_name = st.session_state.get("user_name")
    if user_name:
        return user_name
    
    user = st.session_state.get("user")
    if user:
        user_metadata = getattr(user, 'user_metadata', {})
        user_name = user_metadata.get('full_name', 'Career User')
        if user_name:
            st.session_state["user_name"] = user_name
            return user_name
    
    return "Career User"

# =====================================================
# N8N EVENT SYSTEM
# =====================================================

def trigger_n8n(event_name: str, payload: Optional[Dict] = None) -> bool:
    """
    Sends application events to n8n automation.
    
    Example events:
    application_created, application_status_updated, 
    interview_date_added, application_deleted
    """
    if not N8N_WEBHOOK_URL:
        logger.warning("n8n webhook not configured.")
        return False
    
    user_id = get_user_id()
    user_email = get_user_email()
    user_name = get_user_name()
    
    event_payload = {
        "application": APP_NAME,
        "environment": APP_ENV,
        "event": event_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **(payload or {}),
        "user_id": user_id,
        "user_email": user_email,
        "user_name": user_name
    }
    
    logger.info(f"Sending to n8n: event={event_name}, user_email={user_email}")
    
    for attempt in range(1, N8N_RETRIES + 1):
        try:
            response = requests.post(
                N8N_WEBHOOK_URL,
                json=event_payload,
                timeout=N8N_TIMEOUT
            )
            
            if response.status_code in (200, 201, 202):
                logger.info(f"n8n event sent: {event_name}")
                return True
            
            logger.warning(
                f"n8n failed attempt {attempt}: "
                f"{response.status_code} - {response.text}"
            )
        except requests.exceptions.Timeout:
            logger.error(f"n8n timeout attempt {attempt}")
        except Exception as e:
            logger.error(f"n8n error attempt {attempt}: {e}")
        
        time.sleep(2)
    
    return False

# =====================================================
# VALIDATION
# =====================================================

def validate_text(value: str, field: str) -> str:
    """Validate and clean text input."""
    if not value or not value.strip():
        raise ValueError(f"{field} cannot be empty")
    return value.strip()

# =====================================================
# FIX OLD RECORDS
# =====================================================

def fix_null_user_ids() -> Dict[str, Any]:
    """Update old application records that have null user_id."""
    user_id = get_user_id()
    
    if not user_id:
        return {"success": False, "message": "No user logged in"}
    
    try:
        response = (
            supabase
            .table("applications")
            .select("*")
            .is_("user_id", "null")
            .execute()
        )
        
        if not response.data:
            return {"success": True, "message": "No old records found", "fixed": 0}
        
        count = len(response.data)
        
        for app in response.data:
            (
                supabase
                .table("applications")
                .update({
                    "user_id": user_id, 
                    "user_email": get_user_email()
                })
                .eq("id", app["id"])
                .execute()
            )
        
        logger.info(f"✅ Fixed {count} old records with null user_id")
        
        return {
            "success": True,
            "message": f"Fixed {count} old records",
            "fixed": count
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to fix null user_ids: {e}")
        return {"success": False, "message": str(e)}

# =====================================================
# CHECK DUPLICATE - IMPROVED
# =====================================================

def check_duplicate_application(company: str, role: str, user_id: str) -> Optional[Dict]:
    """
    Check if an application already exists for this user.
    Returns the existing application or None.
    """
    try:
        company_clean = company.strip().lower()
        role_clean = role.strip().lower()
        
        logger.info(f"🔍 Checking duplicate for: '{company_clean}' - '{role_clean}' (User: {user_id})")
        
        # Check for exact match with user_id
        response = (
            supabase
            .table("applications")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )
        
        if not response.data:
            logger.info("📭 No applications found for this user")
            return None
        
        logger.info(f"📊 Found {len(response.data)} applications for user")
        
        # Check each application
        for app in response.data:
            app_company = (app.get("company") or "").strip().lower()
            app_role = (app.get("role") or "").strip().lower()
            
            if app_company == company_clean and app_role == role_clean:
                logger.info(
                    f"⚠️ Duplicate found! ID: {app.get('id')}, "
                    f"Company: {app_company}, Role: {app_role}"
                )
                return app
        
        logger.info("✅ No duplicate found")
        return None
        
    except Exception as e:
        logger.error(f"❌ Duplicate check error: {e}")
        return None

# =====================================================
# CREATE APPLICATION - FIXED
# =====================================================

def add_application(
    company: str,
    role: str,
    job_description: str,
    match_score: int = 0
) -> Dict[str, Any]:
    """
    Add a new job application with duplicate prevention.
    Returns status and application data.
    """
    user_id = get_user_id()
    
    if not user_id:
        return {
            "status": "error",
            "message": "User authentication required. Please log in."
        }
    
    # Clean inputs
    company_clean = company.strip()
    role_clean = role.strip()
    
    # Validate
    try:
        company_clean = validate_text(company_clean, "Company")
        role_clean = validate_text(role_clean, "Role")
        job_description = validate_text(job_description, "Job description")
    except ValueError as e:
        return {"status": "error", "message": str(e)}
    
    # Check duplicate - FIXED: Check by user_id only
    existing = check_duplicate_application(company_clean, role_clean, user_id)
    
    if existing:
        logger.info(f"⚠️ Duplicate application detected: {company_clean} - {role_clean}")
        return {
            "status": "duplicate",
            "message": f"You have already applied to {company_clean} for {role_clean}",
            "application": existing
        }
    
    # Get user email
    user_email = get_user_email()
    if not user_email:
        logger.warning("⚠️ No user email found in session state!")
        # Try to get from user object one more time
        user = st.session_state.get("user")
        if user:
            user_email = getattr(user, 'email', None)
            if user_email:
                st.session_state["user_email"] = user_email
    
    if not user_email:
        user_email = "unknown@example.com"
        logger.warning(f"⚠️ Using fallback email: {user_email}")
    
    # Build application data
    application = {
        "user_id": user_id,
        "user_email": user_email,
        "company": company_clean,
        "role": role_clean,
        "job_description": job_description,
        "status": "Applied",
        "match_score": match_score,
        "interview_date": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    try:
        response = (
            supabase
            .table("applications")
            .insert(application)
            .execute()
        )
        
        if not response.data:
            return {
                "status": "error",
                "message": "Failed to save application - no data returned"
            }
        
        application_id = response.data[0].get("id")
        
        logger.info(f"✅ New application saved: {company_clean} - {role_clean} (ID: {application_id})")
        
        # Send to n8n
        n8n_payload = {
            "application_id": application_id,
            "company": company_clean,
            "role": role_clean,
            "job_description": job_description,
            "user_id": user_id,
            "user_email": user_email,
            "match_score": match_score,
            "status": "Applied",
            "created_at": application["created_at"]
        }
        
        # Fire and forget - don't block on n8n
        try:
            trigger_n8n("application_saved", n8n_payload)
        except Exception as e:
            logger.warning(f"n8n notification failed but app was saved: {e}")
        
        # Update session state to mark as saved
        st.session_state.application_saved = True
        st.session_state.last_application_hash = f"{company_clean}_{role_clean}_{user_id}"
        
        return {
            "status": "success",
            "message": "Application saved successfully",
            "application": response.data[0]
        }
        
    except httpx.ReadTimeout:
        logger.error("⏰ Supabase timeout while saving application")
        return {
            "status": "error",
            "message": "The server is taking too long. Please try again."
        }
    except Exception as e:
        logger.error(f"❌ Create application failed: {e}")
        return {
            "status": "error",
            "message": f"Failed to save application: {str(e)}"
        }

# =====================================================
# GET ALL APPLICATIONS
# =====================================================

def get_applications() -> List[Dict]:
    """Get all applications for the current user."""
    user_id = get_user_id()
    
    if not user_id:
        return []
    
    try:
        response = (
            supabase
            .table("applications")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        
        return response.data or []
        
    except Exception as e:
        logger.error(f"Fetching applications failed: {e}")
        return []

# =====================================================
# GET SINGLE APPLICATION
# =====================================================

def get_application(application_id: str) -> Optional[Dict]:
    """Get a specific application by ID."""
    user_id = get_user_id()
    
    if not user_id:
        return None
    
    try:
        response = (
            supabase
            .table("applications")
            .select("*")
            .eq("id", application_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        
        return response.data
        
    except Exception as e:
        logger.error(f"Get application failed: {e}")
        return None

# =====================================================
# GET APPLICATION BY COMPANY AND ROLE
# =====================================================

def get_application_by_company_role(company: str, role: str, user_id: str) -> Optional[Dict]:
    """Get a specific application by company, role, and user_id."""
    try:
        response = (
            supabase
            .table("applications")
            .select("*")
            .eq("user_id", user_id)
            .eq("company", company)
            .eq("role", role)
            .maybe_single()
            .execute()
        )
        
        return response.data
        
    except Exception as e:
        logger.error(f"Get application by company/role failed: {e}")
        return None

# =====================================================
# UPDATE APPLICATION STATUS
# =====================================================

def update_application_status(application_id: str, status: str) -> Optional[Dict]:
    """Update the status of an application."""
    user_id = get_user_id()
    
    if not user_id:
        return None
    
    try:
        status = validate_text(status, "Status")
    except ValueError as e:
        logger.error(f"Status validation failed: {e}")
        return None
    
    try:
        response = (
            supabase
            .table("applications")
            .update({"status": status})
            .eq("id", application_id)
            .eq("user_id", user_id)
            .execute()
        )
        
        if response.data:
            trigger_n8n("application_status_updated", {
                "application_id": application_id,
                "status": status,
                "user_id": user_id,
                "user_email": get_user_email()
            })
        
        return response.data
        
    except Exception as e:
        logger.error(f"Status update failed: {e}")
        return None

# =====================================================
# UPDATE INTERVIEW DATE
# =====================================================

def update_interview_date(application_id: str, interview_date: str) -> Optional[Dict]:
    """Update the interview date for an application."""
    user_id = get_user_id()
    
    if not user_id:
        return None
    
    try:
        response = (
            supabase
            .table("applications")
            .update({"interview_date": interview_date})
            .eq("id", application_id)
            .eq("user_id", user_id)
            .execute()
        )
        
        if response.data:
            trigger_n8n("interview_date_added", {
                "application_id": application_id,
                "interview_date": interview_date,
                "user_id": user_id,
                "user_email": get_user_email()
            })
        
        return response.data
        
    except Exception as e:
        logger.error(f"Interview date update failed: {e}")
        return None

# =====================================================
# DELETE APPLICATION
# =====================================================

def delete_application(application_id: str) -> bool:
    """Delete an application."""
    user_id = get_user_id()
    
    if not user_id:
        raise Exception("User authentication required.")
    
    try:
        (
            supabase
            .table("applications")
            .delete()
            .eq("id", application_id)
            .eq("user_id", user_id)
            .execute()
        )
        
        trigger_n8n("application_deleted", {
            "application_id": application_id,
            "user_id": user_id,
            "user_email": get_user_email()
        })
        
        return True
        
    except Exception as e:
        logger.error(f"Delete application failed: {e}")
        return False

# =====================================================
# APPLICATION STATISTICS
# =====================================================

def get_application_stats() -> Dict[str, int]:
    """Get statistics for all applications."""
    applications = get_applications()
    
    stats = {
        "total": len(applications),
        "applied": 0,
        "interview": 0,
        "offer": 0,
        "rejected": 0
    }
    
    for app in applications:
        status = (app.get("status") or "").lower()
        
        if status == "applied":
            stats["applied"] += 1
        elif status == "interview":
            stats["interview"] += 1
        elif status == "offer":
            stats["offer"] += 1
        elif status == "rejected":
            stats["rejected"] += 1
    
    return stats

# =====================================================
# CHECK IF APPLICATION IS SAVED
# =====================================================

def is_application_saved(company: str, role: str) -> bool:
    """Check if the current application is already saved."""
    user_id = get_user_id()
    
    if not user_id:
        return False
    
    # Check session state first
    app_hash = f"{company.strip().lower()}_{role.strip().lower()}_{user_id}"
    if st.session_state.get("last_application_hash") == app_hash:
        return st.session_state.get("application_saved", False)
    
    # Check database
    existing = check_duplicate_application(company, role, user_id)
    
    if existing:
        # Update session state
        st.session_state.application_saved = True
        st.session_state.last_application_hash = app_hash
        return True
    
    return False

# =====================================================
# RESET SAVE STATE
# =====================================================

def reset_save_state():
    """Reset the application save state in session."""
    st.session_state.application_saved = False
    st.session_state.last_application_hash = None
    logger.info("🔄 Application save state reset")
