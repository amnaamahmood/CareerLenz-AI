import os
import json
import re
import time
import logging

import requests

from dotenv import load_dotenv
from google import genai
from groq import Groq


# =====================================================
# ENVIRONMENT
# =====================================================

load_dotenv()


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash"
)

N8N_TIMEOUT = int(
    os.getenv(
        "N8N_TIMEOUT",
        "10"
    )
)

MAX_RETRIES = int(
    os.getenv(
        "AI_MAX_RETRIES",
        "3"
    )
)



if not GEMINI_API_KEY:
    raise RuntimeError(
        "Missing GEMINI_API_KEY"
    )


# =====================================================
# LOGGING - MOVED UP BEFORE CLIENT INITIALIZATION
# =====================================================


logging.basicConfig(
    level=logging.INFO
)


logger = logging.getLogger(
    "SkillGap-AI"
)


# =====================================================
# GEMINI CLIENT
# =====================================================


client = genai.Client(
    api_key=GEMINI_API_KEY
)


# =====================================================
# GROQ CLIENT (FALLBACK)
# =====================================================


groq_client = None

if GROQ_API_KEY:
    groq_client = Groq(
        api_key=GROQ_API_KEY
    )
    logger.info("✅ Groq client initialized")
else:
    logger.warning("⚠️ Groq API key not found. Groq fallback disabled.")





# =====================================================
# COMPANY EXTRACTION
# =====================================================


def extract_company_name(
    job_description
):

    if not job_description:
        return "Unknown Company"


    patterns = [

        r"([A-Z][A-Za-z0-9&.\- ]{2,60})\s+is looking for",

        r"([A-Z][A-Za-z0-9&.\- ]{2,60})\s+is hiring",

        r"About\s+([A-Z][A-Za-z0-9&.\- ]{2,60})",

        r"Company[:\-]\s*([A-Z][A-Za-z0-9&.\- ]{2,60})"

    ]


    for pattern in patterns:

        match = re.search(
            pattern,
            job_description,
            re.IGNORECASE
        )


        if match:

            company = match.group(1).strip()


            blacklist = {

                "the",
                "company",
                "team",
                "role",
                "position",
                "job"

            }


            words = [

                word

                for word in company.split()

                if word.lower()
                not in blacklist

            ]


            if words:

                return " ".join(words)



    return "Unknown Company"






# =====================================================
# JSON PARSER
# =====================================================


def parse_json_response(
    text
):

    if not text:
        return None


    try:

        cleaned = text.strip()


        cleaned = re.sub(
            r"```json",
            "",
            cleaned,
            flags=re.I
        )


        cleaned = cleaned.replace(
            "```",
            ""
        ).strip()



        start = cleaned.find(
            "{"
        )


        end = cleaned.rfind(
            "}"
        )


        if start != -1 and end != -1:

            cleaned = cleaned[
                start:end+1
            ]


        return json.loads(
            cleaned
        )


    except Exception as e:

        logger.error(
            f"JSON parsing error: {e}"
        )

        return None






# =====================================================
# N8N WEBHOOK
# =====================================================


def trigger_n8n(
    event,
    payload
):


    if not N8N_WEBHOOK_URL:

        logger.info(
            "N8N disabled"
        )

        return False



    data = {

        "event": event,

        "timestamp":
        time.time(),

        "payload":
        payload

    }



    try:


        response = requests.post(

            N8N_WEBHOOK_URL,

            json=data,

            timeout=N8N_TIMEOUT

        )


        if response.status_code in [

            200,
            201,
            202

        ]:

            logger.info(
                "N8N workflow triggered"
            )

            return True



        logger.warning(
            f"N8N failed {response.status_code}"
        )

        return False



    except Exception as e:


        logger.error(
            f"N8N error {e}"
        )


        return False








# =====================================================
# GROQ FALLBACK
# =====================================================


def analyze_with_groq(prompt):

    if not groq_client:
        raise Exception(
            "Groq API key missing"
        )

    response = groq_client.chat.completions.create(

        model="llama-3.3-70b-versatile",

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0.2

    )

    return response.choices[0].message.content






# =====================================================
# AI ANALYSIS
# =====================================================


def analyze_resume(

    resume_text,

    job_description,

    github_data=None

):


    company = extract_company_name(
        job_description
    )



    prompt = f"""

You are SkillGap AI.

Role:
Senior Technical Recruiter
Engineering Manager
Career Mentor


Analyze candidate resume against job description.


RESUME:

{resume_text}


JOB DESCRIPTION:

{job_description}


GITHUB:

{github_data or "Not provided"}



Return ONLY JSON.

Schema:


{{
"company_name":"",
"job_title":"",
"match_score":0,
"candidate_level":"",
"summary":"",

"requirement_analysis":[
{{
"skill":"",
"category":"technical|tool|soft_skill|education|experience",
"status":"strong_match|partial_match|missing",
"evidence":"",
"missing":"",
"next_step":""
}}
],

"github_review":{{
"score":0,
"summary":"",
"strengths":[],
"weaknesses":[]
}},


"opensource_recommendations":[
{{
"project_name":"",
"why_this_project":"",
"contribution_type":"",
"career_impact":""
}}
],

"portfolio_action_plan":[],

"interview_focus":[],

"mentor_summary":""

}}



Analysis rules:

For every JD requirement:

1. Classify status ONLY as:
- strong_match
- partial_match
- missing

Never use Unknown.

2. Evidence must contain:
- exact resume evidence
- project name
- certification
- technical skill

3. Missing skills must include:
- why it matters
- how to learn it
- suggested portfolio project

4. Do not repeat the same skill twice.

5. Combine related requirements:
Example:
Python + Pandas + NumPy = Data Analysis Stack

Return maximum 8 important requirements only.



Rules:
- Be realistic.
- Never invent skills.
- Compare resume with JD.
- Give recruiter-level feedback.

Output only the 8 most important requirements.

Status MUST be only:
strong_match
partial_match
missing

For strong_match:
- Only provide evidence.
- Keep missing and next_step empty.

For partial_match:
- Explain what evidence is missing.
- Give one improvement step.

For missing:
- Explain why the skill matters.
- Give one practical learning/project suggestion.

Never use:
- Unknown
- Empty skill names
- Generic recommendations

Keep responses concise.
Each explanation must be under 60 words.



Open source recommendations:

Only recommend real projects.

Examples:
- pandas
- numpy
- scikit-learn
- streamlit
- mlflow

Never recommend:
- "Find projects on Kaggle"
- "Look for good first issues"
- "Contribute to beginner friendly libraries"

Every recommendation must contain:
project name
why it matches candidate
specific contribution idea
career benefit

"""



    for attempt in range(
        MAX_RETRIES
    ):


        try:


            response = client.models.generate_content(

                model=GEMINI_MODEL,

                contents=prompt

            )



            analysis = parse_json_response(

                response.text

            )



            if not analysis:

                raise Exception(
                    "Invalid AI JSON"
                )




            if not analysis.get(
                "company_name"
            ):

                analysis["company_name"] = company




            trigger_n8n(

                "resume_analysis_completed",

                {

                    "company":
                    analysis.get(
                        "company_name"
                    ),

                    "job_title":
                    analysis.get(
                        "job_title"
                    ),

                    "match_score":
                    analysis.get(
                        "match_score",
                        0
                    )

                }

            )



            return analysis





        except Exception as e:


            error_msg = str(e)
            
            # Check for quota exceeded error
            if (
                "429" in error_msg
                or "quota" in error_msg
                or "RESOURCE_EXHAUSTED" in error_msg
                or "exceeded your current quota" in error_msg
            ):

                logger.warning(
                    f"⚠️ Gemini quota reached. Switching to Groq..."
                )

                try:

                    groq_response = analyze_with_groq(
                        prompt
                    )

                    analysis = parse_json_response(
                        groq_response
                    )

                    if analysis:

                        logger.info(
                            "✅ Groq fallback successful"
                        )

                        if not analysis.get(
                            "company_name"
                        ):

                            analysis["company_name"] = company

                        trigger_n8n(

                            "resume_analysis_completed",

                            {

                                "company":
                                analysis.get(
                                    "company_name"
                                ),

                                "job_title":
                                analysis.get(
                                    "job_title"
                                ),

                                "match_score":
                                analysis.get(
                                    "match_score",
                                    0
                                )

                            }

                        )

                        return analysis

                except Exception as groq_error:

                    logger.error(
                        f"❌ Groq fallback failed: {groq_error}"
                    )

                    return {

                        "error":
                        "AI service temporarily unavailable. Please try again later.",

                        "quota_error":
                        True,

                        "message":
                        "Both AI models reached their limits. Please try again later."

                    }


            logger.warning(

                f"AI attempt {attempt+1}/{MAX_RETRIES}: {e}"

            )


            time.sleep(2)






    # =================================================
    # SAFE FAILURE RESPONSE
    # =================================================


    failure = {


        "error":

        "AI analysis failed. Please try again later.",


        "company_name":

        company,


        "job_title":

        "Unknown",


        "match_score":

        0,


        "candidate_level":

        "",


        "summary":

        "",



        "requirement_analysis":

        [],



        "github_review":

        {

            "score":0,

            "summary":"",

            "strengths":[],

            "weaknesses":[]

        },



        "opensource_recommendations":

        [],



        "portfolio_action_plan":

        [],



        "interview_focus":

        [],



        "mentor_summary":

        "Analysis service temporarily unavailable. Please try again later."

    }



    return failure
