import streamlit as st

from database import supabase


# =====================================
# CURRENT USER ID
# =====================================

def get_user_id():

    user = st.session_state.get(
        "user",
        None
    )

    if user:

        return user.id

    return None



# =====================================
# SAFE SUPABASE FETCH
# =====================================

def execute_query(query):

    try:

        response = query.execute()

        return response.data or []

    except Exception as e:

        st.error(
            f"Database error: {e}"
        )

        return []



# =====================================
# CAREER ANALYSIS
# =====================================

def get_career_analysis():

    user_id = get_user_id()

    if not user_id:

        return []

    return execute_query(

        supabase

        .table("career_analysis")

        .select("*")

        .eq(
            "user_id",
            user_id
        )

        .order(
            "created_at",
            desc=True
        )

    )



# =====================================
# APPLICATIONS
# =====================================

def get_application_data():

    user_id = get_user_id()

    if not user_id:

        return []

    return execute_query(

        supabase

        .table("applications")

        .select("*")

        .eq(
            "user_id",
            user_id
        )

        .order(
            "created_at",
            desc=True
        )

    )



# =====================================
# INTERVIEW HISTORY
# =====================================

def get_interview_data():

    user_id = get_user_id()

    if not user_id:

        return []

    return execute_query(

        supabase

        .table("interview_sessions")

        .select("*")

        .eq(
            "user_id",
            user_id
        )

        .order(
            "created_at",
            desc=True
        )

    )



# =====================================
# USER PROFILE
# =====================================

def get_profile():

    user_id = get_user_id()

    if not user_id:

        return None


    try:

        response = (

            supabase

            .table("profiles")

            .select("*")

            .eq(
                "id",
                user_id
            )

            .single()

            .execute()

        )


        return response.data


    except Exception:

        return None



# =====================================
# DASHBOARD SUMMARY
# =====================================

def get_dashboard_summary():

    career = get_career_analysis()

    applications = get_application_data()

    interviews = get_interview_data()


    avg_match = 0

    if career:

        scores = [

            item.get(
                "match_score",
                0
            ) or 0

            for item in career

        ]

        avg_match = round(

            sum(scores) / len(scores),

            1

        )


    avg_interview = 0

    if interviews:

        scores = [

            item.get(
                "overall_score",
                item.get(
                    "score",
                    0
                )
            )

            or 0

            for item in interviews

        ]


        avg_interview = round(

            sum(scores) / len(scores),

            1

        )


    return {


        "total_applications":

            len(applications),


        "total_analysis":

            len(career),


        "total_interviews":

            len(interviews),


        "average_match":

            avg_match,


        "average_interview":

            avg_interview

    }