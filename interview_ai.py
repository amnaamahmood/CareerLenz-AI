import os
import json
import time
import logging
import re

from dotenv import load_dotenv
from google import genai


# =====================================================
# ENVIRONMENT
# =====================================================

load_dotenv()



GEMINI_KEY = os.getenv(
    "GEMINI_API_KEY"
)


if not GEMINI_KEY:

    raise RuntimeError(
        "Missing GEMINI_API_KEY"
    )



MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash"
)



client = genai.Client(
    api_key=GEMINI_KEY
)





# =====================================================
# LOGGING
# =====================================================

logging.basicConfig(
    level=logging.INFO
)


logger = logging.getLogger(
    "CareerLensInterviewAI"
)





# =====================================================
# GEMINI CALL
# =====================================================

def generate_ai_response(
    prompt
):


    retries = 3



    for attempt in range(retries):


        try:


            response = client.models.generate_content(

                model=MODEL,

                contents=prompt,

                config={
                    "response_mime_type":
                    "application/json"
                }

            )


            if not response.text:


                raise Exception(
                    "Empty Gemini response"
                )


            # Debug logging
            print("\n===== GEMINI RESPONSE =====")
            print(response.text)
            print("============================\n")

            return response.text



        except Exception as e:



            error = str(e).lower()



            logger.warning(
                f"Gemini attempt {attempt+1}: {e}"
            )



            if (
                "429" in error
                or
                "rate" in error
            ):


                time.sleep(
                    20
                )



            elif "503" in error:


                time.sleep(
                    10
                )


            else:


                break




    return json.dumps({

        "error":
        "AI service unavailable"

    })






# =====================================================
# JSON CLEANER - COMPLETELY REWRITTEN
# =====================================================

def clean_json(
    response
):


    if isinstance(
        response,
        (dict, list)
    ):

        return response


    if not response:
        return {
            "error": "Empty AI response"
        }


    try:

        text = response.strip()


        # remove markdown
        text = re.sub(
            r"```json",
            "",
            text,
            flags=re.I
        )

        text = text.replace(
            "```",
            ""
        ).strip()



        # Find JSON object
        obj_start = text.find("{")
        obj_end = text.rfind("}")


        # Find JSON array
        arr_start = text.find("[")
        arr_end = text.rfind("]")



        if (
            arr_start != -1
            and arr_end != -1
            and (
                obj_start == -1
                or arr_start < obj_start
            )
        ):

            text = text[
                arr_start:
                arr_end+1
            ]


        elif obj_start != -1 and obj_end != -1:

            text = text[
                obj_start:
                obj_end+1
            ]


        return json.loads(text)



    except Exception as e:


        logger.error(
            f"JSON parsing failed: {e}"
        )


        logger.error(
            f"RAW RESPONSE: {response}"
        )


        return {
            "error":
            "Invalid AI response"
        }








# =====================================================
# QUESTION GENERATOR
# =====================================================

def generate_interview_questions(

    resume_text,

    job_description,

    question_count=10

):



    prompt = f"""


You are an expert FAANG interviewer.


Create a personalized interview.

Candidate Resume:

{resume_text[:8000]}


Target Job:

{job_description[:8000]}



Rules:

- Generate exactly {question_count} questions.
- Do not create generic questions.
- Use candidate projects.
- Use job requirements.
- Match difficulty to candidate level.


Distribution:

50% Technical

30% Resume/Project

20% Behavioral



Return ONLY valid JSON.
No markdown.
No explanation.

Return exactly this array format:


[
{{
"category":"",
"difficulty":"",
"question":"",
"expectation":""
}}
]

"""


    response = generate_ai_response(
        prompt
    )


    result = clean_json(
        response
    )



    if isinstance(result,list):


        return result[:question_count]



    return result







# =====================================================
# INTERVIEW EVALUATION
# =====================================================

def evaluate_interview(

    resume_text,

    job_description,

    questions,

    answers

):



    qa = []



    for index,question in enumerate(questions):


        qa.append({

            "question":

            question.get(
                "question",
                ""
            ),


            "answer":

            answers.get(
                index,
                "No answer provided"
            )

        })





    prompt = f"""

You are a senior hiring manager.


Evaluate this technical interview.


Resume:

{resume_text[:6000]}


Job:

{job_description[:6000]}



Interview:


{json.dumps(
    qa,
    indent=2
)}



Return ONLY valid JSON.
No markdown.
No explanation.

Return exactly this format:


{{
"overall_score":0,

"technical_score":0,

"communication_score":0,

"problem_solving_score":0,

"confidence_score":0,


"hire_recommendation":"",


"strengths":[],

"weaknesses":[],

"question_feedback":[

{{
"question":"",
"score":0,
"feedback":"",
"better_answer":""

}}

],


"final_recommendation":"",


"learning_plan":[]

}}

"""


    response = generate_ai_response(
        prompt
    )


    return clean_json(
        response
    )