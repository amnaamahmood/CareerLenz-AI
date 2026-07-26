import os
import logging
import requests

from dotenv import load_dotenv
from database import supabase


# =====================================================
# ENVIRONMENT
# =====================================================

load_dotenv()


N8N_WEBHOOK_URL = os.getenv(
    "N8N_WEBHOOK_URL"
)



# =====================================================
# CONFIG
# =====================================================

INTERVIEW_TABLE = "interview_sessions"



# =====================================================
# LOGGING
# =====================================================

logging.basicConfig(
    level=logging.INFO
)


logger = logging.getLogger(
    "CareerLensInterview"
)





# =====================================================
# N8N AUTOMATION
# =====================================================

def trigger_n8n(
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
# SAVE INTERVIEW
# =====================================================

def save_interview(

    user_id,

    company,

    role,

    job_description,

    questions,

    answers,

    overall_score=0,

    evaluation=None

):


    if not user_id:

        raise Exception(
            "User authentication required"
        )



    evaluation = evaluation or {}



    data = {


        "user_id":
        user_id,


        "company":
        company,


        "role":
        role,


        "job_description":
        job_description,


        "questions":
        questions,


        "answers":
        answers,


        "overall_score":
        overall_score,


        "technical_score":
        evaluation.get(
            "technical_score",
            0
        ),


        "communication_score":
        evaluation.get(
            "communication_score",
            0
        ),


        "problem_solving_score":
        evaluation.get(
            "problem_solving_score",
            0
        ),


        "confidence_score":
        evaluation.get(
            "confidence_score",
            0
        ),


        "strengths":
        evaluation.get(
            "strengths",
            []
        ),


        "weaknesses":
        evaluation.get(
            "weaknesses",
            []
        ),


        "question_feedback":
        evaluation.get(
            "question_feedback",
            []
        ),


        "final_recommendation":
        evaluation.get(
            "final_recommendation",
            ""
        )

    }




    try:


        response = (

            supabase

            .table(
                INTERVIEW_TABLE
            )

            .insert(
                data
            )

            .execute()

        )



        trigger_n8n(

            "interview_completed",

            {

                "user_id":
                user_id,


                "company":
                company,


                "role":
                role,


                "score":
                overall_score

            }

        )



        return response.data



    except Exception as e:


        logger.error(
            f"Interview save failed: {e}"
        )


        raise Exception(
            "Unable to save interview"
        )





# =====================================================
# GET USER INTERVIEWS
# =====================================================

def get_interviews(
    user_id
):


    if not user_id:

        return []



    try:


        response = (

            supabase

            .table(
                INTERVIEW_TABLE
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
            f"Fetch interviews failed: {e}"
        )


        return []





# =====================================================
# GET SINGLE INTERVIEW
# =====================================================

def get_interview_by_id(

    interview_id,

    user_id

):


    try:


        response = (

            supabase

            .table(
                INTERVIEW_TABLE
            )

            .select("*")

            .eq(
                "id",
                interview_id
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
# INTERVIEW STATISTICS
# =====================================================

def get_interview_statistics(
    user_id
):


    interviews = get_interviews(
        user_id
    )



    if not interviews:


        return {


            "total_interviews":
            0,


            "average_score":
            0,


            "best_score":
            0

        }




    scores = [

        item.get(
            "overall_score",
            0
        )
        or 0

        for item in interviews

    ]



    return {


        "total_interviews":
        len(interviews),


        "average_score":
        round(
            sum(scores) / len(scores),
            1
        ),


        "best_score":
        max(scores)

    }





# =====================================================
# DELETE INTERVIEW
# =====================================================

def delete_interview(

    interview_id,

    user_id

):


    if not user_id:

        return False



    try:


        response = (

            supabase

            .table(
                INTERVIEW_TABLE
            )

            .delete()

            .eq(
                "id",
                interview_id
            )

            .eq(
                "user_id",
                user_id
            )

            .execute()

        )


        trigger_n8n(

            "interview_deleted",

            {

                "interview_id":
                interview_id,


                "user_id":
                user_id

            }

        )


        return response.data



    except Exception as e:


        logger.error(
            f"Delete interview failed: {e}"
        )


        return False