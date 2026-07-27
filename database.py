import os
import json
import logging
import requests
import httpx
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any

from dotenv import load_dotenv
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions


# =====================================================
# ENVIRONMENT
# =====================================================

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY")


# =====================================================
# LOGGING
# =====================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("CareerLensDatabase")


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
# TABLE CONFIG
# =====================================================

CAREER_TABLE = "career_analysis"
APPLICATIONS_TABLE = "applications"


# =====================================================
# VALIDATION HELPERS
# =====================================================

def validate_user_id(user_id: Optional[str]) -> str:
    """Validate user_id and return it or raise exception."""
    if not user_id:
        raise ValueError("User authentication required")
    return user_id

def clean_text(text: str) -> str:
    """Clean and sanitize text input."""
    if not text:
        return ""
    return text.strip()


# =====================================================
# N8N EVENT
# =====================================================

def trigger_n8n_workflow(event: str, data: Optional[Dict] = None) -> bool:
    """Trigger n8n webhook workflow."""
    if not N8N_WEBHOOK_URL:
        logger.warning("N8N webhook URL not configured")
        return False
    
    payload = {
        "event": event,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **(data or {})
    }
    
    try:
        response = requests.post(
            N8N_WEBHOOK_URL,
            json=payload,
            timeout=15
        )
        
        if response.status_code in (200, 201, 202):
            logger.info(f"✅ N8N event sent: {event}")
            return True
        else:
            logger.warning(f"⚠️ N8N responded with {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        logger.error(f"⏰ N8N timeout for event: {event}")
        return False
    except Exception as e:
        logger.error(f"❌ N8N error: {e}")
        return False


# =====================================================
# SAVE CAREER ANALYSIS
# =====================================================

def save_analysis(data: Dict[str, Any], user_id: Optional[str]) -> Optional[Dict]:
    """
    Save career analysis data to Supabase.
    Returns the saved record or raises exception.
    """
    user_id = validate_user_id(user_id)
    
    # Clean and prepare payload
    payload = {
        "user_id": user_id,
        "resume_text": clean_text(data.get("resume_text", "")),
        "job_description": clean_text(data.get("job_description", "")),
        "match_score": int(data.get("match_score", 0)),
        "github_score": int(data.get("github_score", 0)),
        "matched_skills": data.get("matched_skills", []),
        "missing_skills": data.get("missing_skills", []),
        "open_source_recommendations": data.get("open_source_recommendations", []),
        "mentor_advice": clean_text(data.get("mentor_advice", "")),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    try:
        response = (
            supabase
            .table(CAREER_TABLE)
            .insert(payload)
            .execute()
        )
        
        if not response.data:
            raise Exception("No data returned from Supabase")
        
        logger.info(f"✅ Career analysis saved for user: {user_id}")
        
        # Send to n8n (fire and forget)
        trigger_n8n_workflow(
            "career_analysis_saved",
            {
                "user_id": user_id,
                "match_score": payload["match_score"],
                "analysis_id": response.data[0].get("id")
            }
        )
        
        return response.data[0]
        
    except httpx.ReadTimeout:
        logger.error(f"⏰ Supabase timeout for user: {user_id}")
        raise Exception("Database timeout. Please try again.")
    except Exception as e:
        logger.error(f"❌ Save analysis failed for user {user_id}: {e}")
        raise Exception(f"Unable to save career analysis: {str(e)}")


# =====================================================
# GET USER ANALYSIS
# =====================================================

def get_user_analysis(user_id: Optional[str]) -> List[Dict]:
    """Get all career analysis records for a user."""
    if not user_id:
        return []
    
    try:
        response = (
            supabase
            .table(CAREER_TABLE)
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        
        return response.data or []
        
    except Exception as e:
        logger.error(f"❌ Fetch analysis failed for user {user_id}: {e}")
        return []


# =====================================================
# GET LATEST ANALYSIS
# =====================================================

def get_latest_analysis(user_id: Optional[str]) -> Optional[Dict]:
    """Get the most recent career analysis for a user."""
    if not user_id:
        return None
    
    try:
        response = (
            supabase
            .table(CAREER_TABLE)
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Get latest analysis failed for user {user_id}: {e}")
        return None


# =====================================================
# GET SINGLE ANALYSIS
# =====================================================

def get_analysis_by_id(analysis_id: str, user_id: Optional[str]) -> Optional[Dict]:
    """Get a specific analysis by ID."""
    user_id = validate_user_id(user_id)
    
    try:
        response = (
            supabase
            .table(CAREER_TABLE)
            .select("*")
            .eq("id", analysis_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        
        return response.data
        
    except Exception as e:
        logger.error(f"❌ Get analysis {analysis_id} failed: {e}")
        return None


# =====================================================
# UPDATE ANALYSIS
# =====================================================

def update_analysis(
    analysis_id: str,
    user_id: Optional[str],
    update_data: Dict[str, Any]
) -> Optional[Dict]:
    """Update an existing analysis record."""
    user_id = validate_user_id(user_id)
    
    # Clean the update data
    clean_data = {}
    for key, value in update_data.items():
        if isinstance(value, str):
            clean_data[key] = clean_text(value)
        elif isinstance(value, list):
            clean_data[key] = value
        elif isinstance(value, (int, float)):
            clean_data[key] = value
        else:
            clean_data[key] = value
    
    clean_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    try:
        response = (
            supabase
            .table(CAREER_TABLE)
            .update(clean_data)
            .eq("id", analysis_id)
            .eq("user_id", user_id)
            .execute()
        )
        
        if not response.data:
            return None
        
        logger.info(f"✅ Analysis {analysis_id} updated for user: {user_id}")
        return response.data[0]
        
    except Exception as e:
        logger.error(f"❌ Update analysis {analysis_id} failed: {e}")
        return None


# =====================================================
# DELETE ANALYSIS
# =====================================================

def delete_analysis(analysis_id: str, user_id: Optional[str]) -> bool:
    """Delete an analysis record."""
    user_id = validate_user_id(user_id)
    
    try:
        (
            supabase
            .table(CAREER_TABLE)
            .delete()
            .eq("id", analysis_id)
            .eq("user_id", user_id)
            .execute()
        )
        
        logger.info(f"✅ Analysis {analysis_id} deleted for user: {user_id}")
        
        # Send to n8n (fire and forget)
        trigger_n8n_workflow(
            "career_analysis_deleted",
            {
                "analysis_id": analysis_id,
                "user_id": user_id
            }
        )
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Delete analysis {analysis_id} failed: {e}")
        return False


# =====================================================
# SAVE APPLICATION (from application_manager)
# =====================================================

def save_application(
    user_id: str,
    company: str,
    role: str,
    job_description: str,
    match_score: int = 0
) -> Dict:
    """
    Save a job application with duplicate prevention.
    Returns the saved application or error.
    """
    user_id = validate_user_id(user_id)
    
    # Clean inputs
    company_clean = clean_text(company)
    role_clean = clean_text(role)
    job_desc_clean = clean_text(job_description)
    
    if not company_clean or not role_clean:
        raise ValueError("Company and role are required")
    
    # Check for duplicate
    try:
        existing = (
            supabase
            .table(APPLICATIONS_TABLE)
            .select("*")
            .eq("user_id", user_id)
            .eq("company", company_clean)
            .eq("role", role_clean)
            .maybe_single()
            .execute()
        )
        
        if existing.data:
            logger.info(f"⚠️ Duplicate application found: {company_clean} - {role_clean}")
            return {
                "status": "duplicate",
                "message": f"Application for {company_clean} ({role_clean}) already exists",
                "application": existing.data
            }
            
    except Exception as e:
        logger.error(f"❌ Duplicate check failed: {e}")
        # Continue anyway - let the database handle it
    
    # Prepare application data
    application_data = {
        "user_id": user_id,
        "company": company_clean,
        "role": role_clean,
        "job_description": job_desc_clean,
        "match_score": match_score,
        "status": "Applied",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    try:
        response = (
            supabase
            .table(APPLICATIONS_TABLE)
            .insert(application_data)
            .execute()
        )
        
        if not response.data:
            raise Exception("No data returned from Supabase")
        
        logger.info(f"✅ Application saved: {company_clean} - {role_clean}")
        
        return {
            "status": "success",
            "message": "Application saved successfully",
            "application": response.data[0]
        }
        
    except Exception as e:
        logger.error(f"❌ Save application failed: {e}")
        raise Exception(f"Failed to save application: {str(e)}")


# =====================================================
# GET USER APPLICATIONS
# =====================================================

def get_user_applications(user_id: Optional[str]) -> List[Dict]:
    """Get all applications for a user."""
    if not user_id:
        return []
    
    try:
        response = (
            supabase
            .table(APPLICATIONS_TABLE)
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        
        return response.data or []
        
    except Exception as e:
        logger.error(f"❌ Get applications failed for user {user_id}: {e}")
        return []


# =====================================================
# UPDATE APPLICATION STATUS
# =====================================================

def update_application_status(
    application_id: str,
    user_id: str,
    status: str
) -> Optional[Dict]:
    """Update the status of an application."""
    user_id = validate_user_id(user_id)
    status_clean = clean_text(status)
    
    if not status_clean:
        raise ValueError("Status is required")
    
    try:
        response = (
            supabase
            .table(APPLICATIONS_TABLE)
            .update({
                "status": status_clean,
                "updated_at": datetime.now(timezone.utc).isoformat()
            })
            .eq("id", application_id)
            .eq("user_id", user_id)
            .execute()
        )
        
        if not response.data:
            return None
        
        logger.info(f"✅ Application {application_id} status updated to: {status_clean}")
        return response.data[0]
        
    except Exception as e:
        logger.error(f"❌ Update application status failed: {e}")
        return None


# =====================================================
# DELETE APPLICATION
# =====================================================

def delete_application_record(application_id: str, user_id: str) -> bool:
    """Delete an application record."""
    user_id = validate_user_id(user_id)
    
    try:
        (
            supabase
            .table(APPLICATIONS_TABLE)
            .delete()
            .eq("id", application_id)
            .eq("user_id", user_id)
            .execute()
        )
        
        logger.info(f"✅ Application {application_id} deleted")
        return True
        
    except Exception as e:
        logger.error(f"❌ Delete application {application_id} failed: {e}")
        return False


# =====================================================
# APPLICATION STATISTICS
# =====================================================

def get_application_stats(user_id: Optional[str]) -> Dict[str, int]:
    """Get statistics for a user's applications."""
    if not user_id:
        return {"total": 0, "applied": 0, "interview": 0, "offer": 0, "rejected": 0}
    
    applications = get_user_applications(user_id)
    
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
# HEALTH CHECK
# =====================================================

def health_check() -> Dict[str, Any]:
    """Check database connectivity and return status."""
    try:
        # Try to query the users table (or any table) to check connection
        response = supabase.table(CAREER_TABLE).select("count").limit(1).execute()
        
        return {
            "status": "healthy",
            "message": "Database connection successful",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
