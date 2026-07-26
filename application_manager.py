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

import streamlit as st

from dotenv import load_dotenv
from supabase import create_client, Client



# =====================================================
# ENVIRONMENT CONFIGURATION
# =====================================================


load_dotenv()



SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


N8N_WEBHOOK_URL = os.getenv(
    "N8N_WEBHOOK_URL"
)


N8N_TIMEOUT = int(
    os.getenv(
        "N8N_TIMEOUT",
        "10"
    )
)


N8N_RETRIES = int(
    os.getenv(
        "N8N_RETRIES",
        "3"
    )
)


APP_NAME = os.getenv(
    "APP_NAME",
    "CareerLens"
)


APP_ENV = os.getenv(
    "APP_ENV",
    "development"
)





if not SUPABASE_URL or not SUPABASE_KEY:

    raise RuntimeError(
        "Missing Supabase environment variables."
    )





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
    level=logging.INFO,
    format=
    "%(asctime)s | %(levelname)s | %(message)s"
)


logger = logging.getLogger(
    "CareerLens-Applications"
)





# =====================================================
# CURRENT USER
# =====================================================


def get_user_id():


    user = st.session_state.get(
        "user"
    )


    if user:

        return user.id



    return None


def get_user_email():

    user = st.session_state.get(
        "user"
    )

    if user:

        return user.email

    return None


def get_user_name():

    user = st.session_state.get(
        "user"
    )

    if user:

        return user.user_metadata.get(
            "full_name",
            "Career User"
        )

    return "Career User"





# =====================================================
# N8N EVENT SYSTEM
# =====================================================


def trigger_n8n(

    event_name,

    payload=None

):


    """
    Sends application events to n8n automation.

    Example events:

    application_created
    application_status_updated
    interview_date_added
    application_deleted

    """


    if not N8N_WEBHOOK_URL:


        logger.warning(
            "n8n webhook not configured."
        )


        return False


    # Get user details
    user_id = get_user_id()
    user_email = get_user_email()
    user_name = get_user_name()

    event_payload = {

        "application": APP_NAME,

        "environment": APP_ENV,

        "event": event_name,

        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),

        "user_id": user_id,

        "user_email": user_email,

        "user_name": user_name,

        "data": payload or {}

    }


    # Log what we're sending for debugging
    logger.info(f"Sending to n8n: event={event_name}, user_email={user_email}")


    for attempt in range(
        1,
        N8N_RETRIES + 1
    ):


        try:


            response = requests.post(


                N8N_WEBHOOK_URL,


                json=event_payload,


                timeout=N8N_TIMEOUT


            )



            if response.status_code in (
                200,
                201,
                202
            ):


                logger.info(
                    f"n8n event sent: {event_name}"
                )


                return True





            logger.warning(

                f"n8n failed attempt {attempt}: "
                f"{response.status_code} - {response.text}"

            )




        except Exception as e:


            logger.error(

                f"n8n error attempt {attempt}: {e}"

            )



        time.sleep(2)




    return False






# =====================================================
# VALIDATION
# =====================================================


def validate_text(
    value,
    field
):


    if not value or not value.strip():

        raise ValueError(
            f"{field} cannot be empty"
        )


    return value.strip()





# =====================================================
# CHECK DUPLICATE APPLICATION - FIXED FOR NULL USER_ID
# =====================================================


def check_duplicate_application(company, role, user_id):

    try:

        company_clean = company.strip().lower()
        role_clean = role.strip().lower()

        logger.info(f"🔍 Checking duplicate for: '{company_clean}' - '{role_clean}' (User: {user_id})")

        # Get ALL applications (no user_id filter)
        response = (
            supabase
            .table("applications")
            .select("*")
            .execute()
        )

        if not response.data:
            logger.info("📭 No applications found in database")
            return None

        logger.info(f"📊 Found {len(response.data)} total applications in database")

        # Check each application for duplicate
        for app in response.data:

            app_company = (
                app.get("company") or ""
            ).strip().lower()

            app_role = (
                app.get("role") or ""
            ).strip().lower()

            # Check if company and role match
            if (
                app_company == company_clean
                and app_role == role_clean
            ):

                # Check if user_id matches OR old data has null user_id
                app_user_id = app.get("user_id")
                
                if (
                    app_user_id == user_id
                    or app_user_id is None
                ):

                    logger.info(
                        f"⚠️ Duplicate found! ID: {app.get('id')}, "
                        f"User: {app_user_id}, "
                        f"Company: {app_company}, "
                        f"Role: {app_role}"
                    )

                    return app
                else:
                    logger.info(
                        f"⏭️ Skipping app {app.get('id')} - user_id mismatch "
                        f"({app_user_id} vs {user_id})"
                    )

        logger.info("✅ No duplicate found")
        return None


    except Exception as e:

        logger.error(
            f"❌ Duplicate check error: {e}"
        )

        return None





# =====================================================
# CREATE APPLICATION (with duplicate check)
# =====================================================


def add_application(

    company,

    role,

    job_description,

    match_score=0

):


    user_id = get_user_id()



    if not user_id:

        raise Exception(
            "User authentication required."
        )


    # Clean the inputs
    company_clean = company.strip()
    role_clean = role.strip()


    # Check if application already exists
    existing = check_duplicate_application(
        company_clean,
        role_clean,
        user_id
    )

    if existing:
        logger.info(f"⚠️ Duplicate application detected: {company_clean} - {role_clean}")
        return {
            "status": "duplicate",
            "message": "You have already applied to this position",
            "application": existing
        }


    # Get user email
    user_email = get_user_email()
    
    if not user_email:
        logger.warning("⚠️ No user email found in session state!")
        user_email = "unknown@example.com"


    company = validate_text(
        company_clean,
        "Company"
    )


    role = validate_text(
        role_clean,
        "Role"
    )


    job_description = validate_text(
        job_description,
        "Job description"
    )




    application = {

        "user_id": user_id,

        "user_email": user_email,

        "company": company,

        "role": role,

        "job_description": job_description,

        "status": "Applied",

        "interview_date": None

    }




    try:


        response = (

            supabase

            .table(
                "applications"
            )

            .insert(
                application
            )

            .execute()

        )




        application_id = None



        if response.data:

            application_id = (

                response.data[0]

                .get(
                    "id"
                )

            )


        # Build the data payload for n8n
        n8n_payload = {

            "application_id": application_id,

            "company": company,

            "role": role,

            "job_description": job_description,

            "user_id": user_id,

            "user_email": user_email,

            "match_score": match_score,

            "status": "Applied",

            "created_at": datetime.now(
                timezone.utc
            ).isoformat()

        }


        # Log what we're sending
        logger.info(f"✅ New application saved: {company} - {role} (ID: {application_id})")


        trigger_n8n(

            "application_saved",

            n8n_payload

        )




        return {
            "status": "success",
            "message": "Application saved successfully",
            "application": response.data[0] if response.data else None
        }





    except Exception as e:


        logger.error(
            f"❌ Create application failed: {e}"
        )


        raise Exception(
            str(e)
        )






# =====================================================
# GET ALL APPLICATIONS
# =====================================================


def get_applications():


    user_id = get_user_id()



    if not user_id:

        return []





    try:


        response = (

            supabase

            .table(
                "applications"
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
            f"Fetching applications failed: {e}"
        )


        return []







# =====================================================
# GET SINGLE APPLICATION
# =====================================================


def get_application(

    application_id

):


    user_id = get_user_id()



    if not user_id:

        return None




    try:


        response = (

            supabase

            .table(
                "applications"
            )

            .select("*")

            .eq(
                "id",
                application_id
            )

            .eq(
                "user_id",
                user_id
            )

            .single()

            .execute()

        )



        return response.data





    except Exception as e:


        logger.error(
            f"Get application failed: {e}"
        )


        return None






# =====================================================
# GET APPLICATION BY COMPANY AND ROLE
# =====================================================


def get_application_by_company_role(

    company,
    role,
    user_id

):

    """
    Get a specific application by company, role, and user_id.
    """

    try:

        response = (

            supabase

            .table(
                "applications"
            )

            .select("*")

            .eq(
                "user_id",
                user_id
            )

            .eq(
                "company",
                company
            )

            .eq(
                "role",
                role
            )

            .maybe_single()

            .execute()

        )


        return response.data



    except Exception as e:


        logger.error(
            f"Get application by company/role failed: {e}"
        )


        return None






# =====================================================
# UPDATE APPLICATION STATUS
# =====================================================


def update_application_status(

    application_id,

    status

):


    user_id = get_user_id()



    if not user_id:

        return False




    status = validate_text(
        status,
        "Status"
    )




    try:


        response = (

            supabase

            .table(
                "applications"
            )

            .update(

                {

                    "status":

                    status

                }

            )

            .eq(

                "id",

                application_id

            )

            .eq(

                "user_id",

                user_id

            )

            .execute()

        )





        trigger_n8n(

            "application_status_updated",

            {

                "application_id": application_id,

                "status": status,
                
                "user_id": user_id,

                "user_email": get_user_email()

            }

        )




        return response.data





    except Exception as e:


        logger.error(
            f"Status update failed: {e}"
        )


        return False







# =====================================================
# UPDATE INTERVIEW DATE
# =====================================================


def update_interview_date(

    application_id,

    interview_date

):


    user_id = get_user_id()



    if not user_id:

        return False





    try:


        response = (

            supabase

            .table(
                "applications"
            )

            .update(

                {

                    "interview_date":

                    interview_date

                }

            )

            .eq(

                "id",

                application_id

            )

            .eq(

                "user_id",

                user_id

            )

            .execute()

        )




        trigger_n8n(

            "interview_date_added",

            {

                "application_id": application_id,

                "interview_date": interview_date,
                
                "user_id": user_id,

                "user_email": get_user_email()

            }

        )




        return response.data





    except Exception as e:


        logger.error(
            f"Interview date update failed: {e}"
        )


        return False







# =====================================================
# DELETE APPLICATION
# =====================================================


def delete_application(

    application_id

):


    user_id = get_user_id()



    if not user_id:

        raise Exception(
            "User authentication required."
        )





    try:


        (

            supabase

            .table(
                "applications"
            )

            .delete()

            .eq(
                "id",
                application_id
            )

            .eq(
                "user_id",
                user_id
            )

            .execute()

        )





        trigger_n8n(

            "application_deleted",

            {

                "application_id": application_id,
                
                "user_id": user_id,

                "user_email": get_user_email()

            }

        )




        return True





    except Exception as e:


        logger.error(
            f"Delete application failed: {e}"
        )


        return False






# =====================================================
# APPLICATION STATISTICS
# =====================================================


def get_application_stats():


    applications = get_applications()



    stats = {


        "total":

        len(applications),


        "applied":

        0,


        "interview":

        0,


        "offer":

        0,


        "rejected":

        0

    }





    for app in applications:


        status = (

            app.get(
                "status",
                ""
            )

            .lower()

        )



        if status == "applied":

            stats["applied"] += 1



        elif status == "interview":

            stats["interview"] += 1



        elif status == "offer":

            stats["offer"] += 1



        elif status == "rejected":

            stats["rejected"] += 1





    return stats
