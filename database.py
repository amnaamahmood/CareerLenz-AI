import os
import json
import logging
import requests

from dotenv import load_dotenv
from supabase import create_client, Client


# =====================================================
# ENVIRONMENT
# =====================================================

load_dotenv()


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")


if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "Missing SUPABASE_URL or SUPABASE_KEY"
    )



# =====================================================
# LOGGING
# =====================================================

logging.basicConfig(
    level=logging.INFO
)

logger = logging.getLogger(
    "CareerLensDatabase"
)



# =====================================================
# SUPABASE CLIENT
# =====================================================

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)



# =====================================================
# TABLE CONFIG
# =====================================================

CAREER_TABLE = "career_analysis"





# =====================================================
# USER SESSION HANDLER
# =====================================================

def get_current_user_id(user=None):

    """
    User id is passed from app layer.
    Avoids database depending on Streamlit.
    """

    if user:

        return user.id


    return None





# =====================================================
# N8N EVENT
# =====================================================

def trigger_n8n_workflow(
    event,
    data=None
):


    if not N8N_WEBHOOK_URL:

        return False



    payload = {

        "event": event,

        **(data or {})

    }



    try:

        response = requests.post(

            N8N_WEBHOOK_URL,

            json=payload,

            timeout=15

        )


        return response.status_code in (
            200,
            201,
            202
        )



    except Exception as e:


        logger.error(
            f"N8N error: {e}"
        )


        return False





# =====================================================
# SAVE CAREER ANALYSIS
# =====================================================

def save_analysis(
    data,
    user_id
):


    if not user_id:

        raise Exception(
            "User authentication required"
        )



    payload = {


        "user_id": user_id,


        "resume_text":
        data.get(
            "resume_text",
            ""
        ),


        "job_description":
        data.get(
            "job_description",
            ""
        ),


        "match_score":
        data.get(
            "match_score",
            0
        ),


        "github_score":
        data.get(
            "github_score",
            0
        ),


        "matched_skills":
        data.get(
            "matched_skills",
            []
        ),


        "missing_skills":
        data.get(
            "missing_skills",
            []
        ),


        "open_source_recommendations":
        data.get(
            "open_source_recommendations",
            []
        ),


        "mentor_advice":
        data.get(
            "mentor_advice",
            ""
        )

    }



    try:


        response = (

            supabase

            .table(
                CAREER_TABLE
            )

            .insert(
                payload
            )

            .execute()

        )



        trigger_n8n_workflow(

            "career_analysis_saved",

            {

                "user_id": user_id,

                "match_score":
                payload["match_score"]

            }

        )


        return response.data



    except Exception as e:


        logger.error(
            f"Save analysis failed: {e}"
        )


        raise Exception(
            "Unable to save career analysis"
        )





# =====================================================
# GET USER ANALYSIS
# =====================================================

def get_user_analysis(
    user_id
):


    if not user_id:

        return []



    try:


        response = (

            supabase

            .table(
                CAREER_TABLE
            )

            .select("*")

            .eq(
                "user_id",
                user_id
            )

            .order(
                "created_at",
                desc=True
            )

            .execute()

        )



        return response.data or []



    except Exception as e:


        logger.error(
            f"Fetch analysis failed: {e}"
        )


        return []





# =====================================================
# GET SINGLE ANALYSIS
# =====================================================

def get_analysis_by_id(
    analysis_id,
    user_id
):


    try:


        response = (

            supabase

            .table(
                CAREER_TABLE
            )

            .select("*")

            .eq(
                "id",
                analysis_id
            )

            .eq(
                "user_id",
                user_id
            )

            .single()

            .execute()

        )


        return response.data



    except Exception:


        return None





# =====================================================
# UPDATE ANALYSIS
# =====================================================

def update_analysis(
    analysis_id,
    user_id,
    update_data
):


    try:


        response = (

            supabase

            .table(
                CAREER_TABLE
            )

            .update(
                update_data
            )

            .eq(
                "id",
                analysis_id
            )

            .eq(
                "user_id",
                user_id
            )

            .execute()

        )


        return response.data



    except Exception as e:


        logger.error(
            f"Update failed: {e}"
        )


        return False





# =====================================================
# DELETE ANALYSIS
# =====================================================

def delete_analysis(
    analysis_id,
    user_id
):


    try:


        (

            supabase

            .table(
                CAREER_TABLE
            )

            .delete()

            .eq(
                "id",
                analysis_id
            )

            .eq(
                "user_id",
                user_id
            )

            .execute()

        )



        trigger_n8n_workflow(

            "career_analysis_deleted",

            {

                "analysis_id":
                analysis_id,

                "user_id":
                user_id

            }

        )


        return True



    except Exception as e:


        logger.error(
            f"Delete failed: {e}"
        )


        return False