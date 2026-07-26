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


    event_payload = {

        "application": APP_NAME,

        "environment": APP_ENV,

        "event": event_name,

        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),

        "user_id": get_user_id(),

        "user_email": st.session_state.user.email,

        "data": payload or {}

    }




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
                f"{response.status_code}"

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
# CREATE APPLICATION
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




    company = validate_text(
        company,
        "Company"
    )


    role = validate_text(
        role,
        "Role"
    )


    job_description = validate_text(
        job_description,
        "Job description"
    )




    application = {

        "user_id": user_id,

        "user_email": st.session_state.user.email,

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





        trigger_n8n(

            "application_saved",

            {

                "application_id": application_id,

                "company": company,

                "role": role,

                "job_description": job_description,

                "user_id": user_id,

                "user_email": st.session_state.user.email,

                "match_score": match_score

            }

        )




        return response.data





    except Exception as e:


        logger.error(
            f"Create application failed: {e}"
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


                "application_id":

                application_id,


                "status":

                status,
                
                "user_email":  # Include user_email in status update too
                get_user_email()

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


                "application_id":

                application_id,


                "interview_date":

                interview_date,
                
                "user_email":  # Include user_email in interview update too
                get_user_email()

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


                "application_id":

                application_id,
                
                "user_email":  # Include user_email in delete too
                get_user_email()

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
