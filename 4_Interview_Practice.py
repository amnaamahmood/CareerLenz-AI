import streamlit as st

from interview_manager import save_interview

from interview_ai import (
    generate_interview_questions,
    evaluate_interview
)


# =====================================
# PAGE CONFIG
# =====================================

st.set_page_config(
    page_title="AI Interview Practice | CareerLens AI",
    page_icon="🎤",
    layout="wide"
)



# =====================================
# PREMIUM STYLE
# =====================================

st.markdown(
"""
<style>


.stApp{

background:
radial-gradient(
circle at top right,
#172554,
#070B14 45%
);

}



.main-title{

font-size:42px;
font-weight:800;
color:#F8FAFC;

}



.subtitle{

font-size:18px;
color:#94A3B8;

}



.interview-card{

background:
rgba(17,24,39,0.85);

border:

1px solid rgba(255,255,255,0.08);

border-radius:22px;

padding:28px;

margin-bottom:20px;

}



.question{

font-size:24px;

font-weight:700;

color:white;

}



.info-card{

background:
linear-gradient(
135deg,
#312E81,
#1D4ED8
);

padding:25px;

border-radius:20px;

color:white;

}



.score-card{

background:#111827;

border:1px solid #334155;

border-radius:18px;

padding:20px;

text-align:center;

}



</style>
""",
unsafe_allow_html=True
)




# =====================================
# HEADER
# =====================================

st.markdown(
"""
<div class="main-title">
🎤 AI Interview Practice
</div>


<div class="subtitle">

Practice realistic interviews generated from your resume,
projects and target job requirements.

</div>

""",
unsafe_allow_html=True
)


st.divider()





# =====================================
# VALIDATE PROFILE
# =====================================

if "analysis" not in st.session_state:


    st.warning(
        "Complete Career Analysis first to generate personalized interview questions."
    )

    st.stop()



resume_text = st.session_state.get(
    "resume_text",
    ""
)


job_description = st.session_state.get(
    "job_description",
    ""
)



analysis = st.session_state.get(
    "analysis",
    {}
)




# dynamic company + role extraction

company = analysis.get(
    "company_name",
    "Unknown Company"
)


role = analysis.get(
    "job_title",
    "Unknown Role"
)




# =====================================
# SESSION STATE
# =====================================

defaults={

    "questions":None,

    "current_question":0,

    "answers":{},

    "evaluation":None,

    "interview_saved":False

}



for key,value in defaults.items():

    if key not in st.session_state:

        st.session_state[key]=value






# =====================================
# CREATE INTERVIEW
# =====================================


if st.session_state.questions is None:


    st.markdown(
    """

    <div class="info-card">


    <h3>
    AI Interview Engine
    </h3>


    Generates questions from:


    <br><br>


    ✓ Resume skills


    <br>

    ✓ Projects


    <br>

    ✓ Job description


    <br>

    ✓ Required technologies


    <br>

    ✓ Expected role level


    </div>


    """,

    unsafe_allow_html=True

    )



    st.write("")



    if st.button(

        "🚀 Generate Personalized Interview",

        type="primary",

        use_container_width=True

    ):



        with st.spinner(

            "AI interviewer is preparing questions..."

        ):



            questions = generate_interview_questions(

                resume_text,

                job_description

            )




        if isinstance(questions,dict) and "error" in questions:


            st.error(
                questions["error"]
            )

            st.stop()



        if not isinstance(
            questions,
            list
        ) or len(questions)==0:


            st.error(
                "AI failed to generate interview questions."
            )

            st.stop()



        st.session_state.questions = questions


        st.session_state.current_question = 0


        st.session_state.answers = {}


        st.session_state.evaluation = None


        st.rerun()



    st.stop()






# =====================================
# ACTIVE INTERVIEW
# =====================================


questions = st.session_state.questions


current = st.session_state.current_question



total = len(questions)



if current >= total:

    current = total - 1


    st.session_state.current_question=current




progress=(current+1)/total



st.progress(progress)



st.caption(
f"Question {current+1} of {total}"
)



question = questions[current]





st.markdown(

f"""

<div class="interview-card">


<div class="question">

{question.get("category","Interview")}

</div>


<br>


<b>
Difficulty:
</b>

{question.get("difficulty","Medium")}


<br><br>


<b>
Question:
</b>


<br><br>


{question.get("question","")}


<br><br>


<b>
Interviewer Expectation:
</b>


<br>


{question.get("expectation","")}


</div>


""",

unsafe_allow_html=True

)





# =====================================
# ANSWER BOX
# =====================================


answer_key=f"answer_{current}"



if answer_key not in st.session_state:


    st.session_state[answer_key]=st.session_state.answers.get(

        current,

        ""

    )



st.text_area(

    "Your Answer",

    key=answer_key,

    height=230,

    placeholder="Answer like a real technical interview..."

)





def save_answer():

    st.session_state.answers[current] = st.session_state.get(

        answer_key,

        ""

    )


# =====================================
# NAVIGATION
# =====================================


col1,col2,col3 = st.columns(3)



with col1:


    if st.button(

        "⬅ Previous",

        use_container_width=True

    ):


        save_answer()


        if current > 0:


            st.session_state.current_question -= 1

            st.rerun()





with col2:


    if st.button(

        "⏭ Skip",

        use_container_width=True

    ):


        save_answer()


        if current < total - 1:


            st.session_state.current_question += 1

            st.rerun()





with col3:


    if st.button(

        "Next ➡",

        use_container_width=True

    ):


        save_answer()


        if current < total - 1:


            st.session_state.current_question += 1

            st.rerun()






# =====================================
# EVALUATE INTERVIEW
# =====================================


if current == total - 1:


    st.divider()



    if st.button(

        "🤖 Evaluate My Interview",

        type="primary",

        use_container_width=True

    ):



        save_answer()



        with st.spinner(

            "AI is reviewing your performance..."

        ):



            result = evaluate_interview(

                resume_text,

                job_description,

                questions,

                st.session_state.answers

            )



        if isinstance(result,dict) and "error" in result:


            st.error(
                result["error"]
            )


        else:


            st.session_state.evaluation = result




            if not st.session_state.interview_saved:


                try:



                    save_interview(

                        company,

                        role,

                        job_description,

                        questions,

                        st.session_state.answers,

                        result.get(

                            "overall_score",

                            0

                        ),

                        result

                    )



                    st.session_state.interview_saved=True



                except Exception as e:



                    st.error(

                        f"Interview save failed: {e}"

                    )



        st.rerun()






# =====================================
# REPORT
# =====================================


if st.session_state.evaluation:


    report = st.session_state.evaluation



    st.divider()



    st.header(
        "📊 Interview Performance"
    )



    c1,c2,c3,c4 = st.columns(4)



    metrics=[


        (

            "Overall",

            report.get(
                "overall_score",
                0
            )

        ),



        (

            "Technical",

            report.get(
                "technical_score",
                0
            )

        ),



        (

            "Communication",

            report.get(
                "communication_score",
                0
            )

        ),



        (

            "Confidence",

            report.get(
                "confidence_score",
                0
            )

        )

    ]




    for col,(title,value) in zip(

        [c1,c2,c3,c4],

        metrics

    ):



        with col:



            st.markdown(

            f"""

            <div class="score-card">


            <h2>

            {value}%

            </h2>


            <p>

            {title}

            </p>


            </div>

            """,

            unsafe_allow_html=True

            )






    st.divider()



    st.subheader(
        "💪 Strengths"
    )



    strengths = report.get(

        "strengths",

        []

    )



    if strengths:


        for item in strengths:


            st.success(item)


    else:


        st.info(
            "No strengths available."
        )






    st.subheader(
        "📌 Improvements"
    )



    weaknesses = report.get(

        "weaknesses",

        []

    )



    if weaknesses:


        for item in weaknesses:


            st.warning(item)


    else:


        st.info(
            "No improvement areas available."
        )






    st.subheader(
        "📝 Question Feedback"
    )



    feedback = report.get(

        "question_feedback",

        []

    )



    if feedback:


        for item in feedback:



            with st.expander(

                item.get(

                    "question",

                    "Question"

                )

            ):



                st.write(

                    "**Score:**",

                    item.get(

                        "score",

                        0

                    )

                )


                st.write(

                    "**Feedback:**"

                )


                st.write(

                    item.get(

                        "feedback",

                        ""

                    )

                )


                st.write(

                    "**Better Answer:**"

                )


                st.write(

                    item.get(

                        "better_answer",

                        ""

                    )

                )





    st.subheader(
        "🎯 Learning Plan"
    )



    learning_plan = report.get(

        "learning_plan",

        []

    )



    for item in learning_plan:


        st.write(

            "• " + item

        )





    st.info(

        report.get(

            "final_recommendation",

            ""

        )

    )







# =====================================
# RESET INTERVIEW
# =====================================


st.divider()



if st.button(

    "🔄 Start New Interview",

    use_container_width=True

):



    remove_keys = [

        "questions",

        "current_question",

        "answers",

        "evaluation",

        "interview_saved"

    ]



    for key in remove_keys:


        if key in st.session_state:


            del st.session_state[key]



    for key in list(

        st.session_state.keys()

    ):


        if key.startswith(

            "answer_"

        ):


            del st.session_state[key]



    st.rerun()





# =====================================
# FOOTER
# =====================================


st.divider()



st.caption(

"CareerLens AI • AI Powered Interview Intelligence"

)