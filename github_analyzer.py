import os
import requests
import logging

from dotenv import load_dotenv



# =====================================================
# ENVIRONMENT CONFIG
# =====================================================

load_dotenv()



GITHUB_API_URL = os.getenv(
    "GITHUB_API_URL",
    "https://api.github.com"
)


GITHUB_TOKEN = os.getenv(
    "GITHUB_TOKEN",
    ""
)





# =====================================================
# LOGGING
# =====================================================

logging.basicConfig(
    level=logging.INFO
)


logger = logging.getLogger(
    "CareerLens-GitHub"
)







# =====================================================
# GITHUB HEADERS
# =====================================================


def github_headers():

    headers = {

        "Accept":
        "application/vnd.github.mercy-preview+json",

        "User-Agent":
        "CareerLens-AI"

    }


    if GITHUB_TOKEN:

        headers["Authorization"] = (

            f"Bearer {GITHUB_TOKEN}"

        )


    return headers








# =====================================================
# USERNAME CLEANING
# =====================================================


def clean_username(
    username
):


    if not username:

        return ""



    username = username.strip()



    remove_patterns = [

        "https://github.com/",

        "http://github.com/",

        "github.com/"

    ]



    for pattern in remove_patterns:

        username = username.replace(

            pattern,

            ""

        )



    username = username.strip(
        "/"
    )


    return username







# =====================================================
# SAFE REQUEST
# =====================================================


def github_request(
    endpoint,
    params=None
):


    try:


        response = requests.get(

            f"{GITHUB_API_URL}{endpoint}",

            headers=github_headers(),

            params=params,

            timeout=15

        )


        # Handle rate limiting
        if response.status_code == 403:

            logger.warning(
                "GitHub API rate limit reached"
            )

            return {
                "error":
                "GitHub API limit reached"
            }


        if response.status_code != 200:

            return None



        return response.json()



    except requests.exceptions.Timeout:


        logger.warning(
            "GitHub API timeout"
        )

        return None



    except Exception as e:


        logger.error(
            f"GitHub API error: {e}"
        )


        return None







# =====================================================
# GITHUB INSIGHTS
# =====================================================


def github_insights(
    repos,
    languages,
    followers
):

    strengths = []
    weaknesses = []

    # Repository count
    repo_count = len(repos)

    if repo_count >= 5:
        strengths.append(
            "Maintains multiple public projects"
        )
    else:
        weaknesses.append(
            "Limited public portfolio"
        )

    # Language diversity
    language_count = len(languages)

    if language_count >= 3:
        strengths.append(
            "Shows language diversity"
        )
    else:
        weaknesses.append(
            "Limited language variety"
        )

    # Documentation quality
    readme_count = sum(
        1 for r in repos
        if r.get("has_readme", False)
    )

    if repo_count > 0:
        readme_ratio = readme_count / repo_count

        if readme_ratio >= 0.7:
            strengths.append(
                "Good documentation coverage"
            )
        elif readme_ratio < 0.3:
            weaknesses.append(
                "Many repositories lack documentation"
            )

    # Description quality
    description_count = sum(
        1 for r in repos
        if r.get("description") and
        len(r.get("description", "")) > 10
    )

    if repo_count > 0:
        desc_ratio = description_count / repo_count

        if desc_ratio >= 0.7:
            strengths.append(
                "Projects have clear descriptions"
            )
        elif desc_ratio < 0.3:
            weaknesses.append(
                "Most projects lack proper descriptions"
            )

    # Followers
    if followers >= 50:
        strengths.append(
            "Active GitHub community presence"
        )
    elif followers < 5:
        weaknesses.append(
            "Limited GitHub network"
        )

    # Project activity
    active_repos = sum(
        1 for r in repos
        if r.get("has_activity", False)
    )

    if repo_count > 0:
        active_ratio = active_repos / repo_count

        if active_ratio >= 0.6:
            strengths.append(
                "Maintains active projects"
            )
        elif active_ratio < 0.3:
            weaknesses.append(
                "Many projects appear inactive"
            )

    return {
        "strengths": strengths[:5],
        "weaknesses": weaknesses[:5]
    }







# =====================================================
# GITHUB ANALYZER
# =====================================================


def analyze_github(
    username
):


    try:


        username = clean_username(
            username
        )



        if not username:


            return {

                "error":
                "GitHub username required"

            }





        # =============================
        # PROFILE
        # =============================


        profile = github_request(

            f"/users/{username}"

        )


        # Check if profile is error dict
        if isinstance(profile, dict) and profile.get("error"):
            return profile


        if not profile:


            return {

                "error":
                "GitHub profile not found"

            }





        # =============================
        # REPOSITORIES
        # =============================


        repos = github_request(

            f"/users/{username}/repos",

            {

                "sort":
                "updated",

                "per_page":
                100

            }

        )


        # Check if repos is error dict
        if isinstance(repos, dict) and repos.get("error"):
            return repos


        if repos is None:


            return {

                "error":
                "Unable to fetch repositories"

            }





        projects = []

        languages = {}

        total_stars = 0

        total_forks = 0



        documented_projects = 0





        # =============================
        # ANALYZE REPOS
        # =============================


        for repo in repos:

            repo_name = repo.get("name", "")

            # Get README
            readme = github_request(
                f"/repos/{username}/{repo_name}/readme"
            )

            has_readme = bool(readme and not isinstance(readme, dict) or 
                            (isinstance(readme, dict) and not readme.get("error")))

            # Get topics
            topics = repo.get(
                "topics",
                []
            )

            # Check activity
            created_at = repo.get(
                "created_at"
            )

            updated_at = repo.get(
                "updated_at"
            )

            # Consider active if updated in last 6 months
            has_activity = False

            if updated_at:
                try:
                    from datetime import datetime
                    updated = datetime.fromisoformat(
                        updated_at.replace('Z', '+00:00')
                    )
                    now = datetime.now().astimezone()
                    days_since_update = (now - updated).days
                    has_activity = days_since_update < 180
                except:
                    has_activity = False

            language = repo.get(
                "language"
            )

            if language:
                languages[language] = (
                    languages.get(language, 0) + 1
                )

            stars = repo.get(
                "stargazers_count",
                0
            )

            forks = repo.get(
                "forks_count",
                0
            )

            total_stars += stars
            total_forks += forks

            if repo.get("description"):
                documented_projects += 1

            projects.append(
                {
                    "name": repo.get("name", ""),
                    "description": repo.get("description") or "No description available",
                    "language": language or "Unknown",
                    "stars": stars,
                    "forks": forks,
                    "url": repo.get("html_url", ""),
                    "created": created_at,
                    "last_updated": updated_at,
                    "has_readme": has_readme,
                    "has_activity": has_activity,
                    "topics": topics[:10]
                }
            )





        # =============================
        # SORT PROJECTS - IMPROVED
        # =============================


        projects.sort(

            key=lambda x:
            (
                bool(x.get("description") and 
                     len(x.get("description", "")) > 10),
                bool(x.get("has_readme", False)),
                bool(x.get("has_activity", False)),
                bool(x.get("language") != "Unknown"),
                x.get("last_updated", ""),
                x.get("stars", 0),
                x.get("forks", 0)
            ),
            reverse=True

        )







        # =============================
        # GITHUB INSIGHTS
        # =============================


        insights = github_insights(
            repos,
            languages,
            profile.get("followers", 0)
        )





        # =============================
        # FINAL RESPONSE
        # =============================


        return {

            "username":
            profile.get("login", username),

            "name":
            profile.get("name") or "Not Provided",

            "bio":
            profile.get("bio") or "No bio available",

            "profile_url":
            profile.get("html_url"),

            "followers":
            profile.get("followers", 0),

            "following":
            profile.get("following", 0),

            "public_repositories":
            profile.get("public_repos", 0),

            "total_projects":
            len(projects),

            "projects":
            projects[:10],

            "languages":
            sorted(
                languages,
                key=languages.get,
                reverse=True
            ),

            "language_usage":
            languages,

            "total_stars":
            total_stars,

            "total_forks":
            total_forks,

            "documentation_rate":
            round(
                (documented_projects / len(repos) * 100)
                if repos
                else 0,
                2
            ),

            "github_strength":
            calculate_github_score(
                profile,
                repos,
                languages,
                total_stars
            ),

            "strengths":
            insights.get("strengths", []),

            "weaknesses":
            insights.get("weaknesses", [])

        }





    except Exception as e:


        logger.error(
            f"GitHub analysis failed: {e}"
        )


        return {

            "error":
            str(e)

        }








# =====================================================
# GITHUB QUALITY SCORE - IMPROVED
# =====================================================


def calculate_github_score(

    user,

    repos,

    languages,

    stars

):


    score = 0

    repo_count = len(repos)

    # Repository count - less weight
    if repo_count >= 10:
        score += 10
    elif repo_count >= 5:
        score += 7
    elif repo_count > 0:
        score += 3

    # Language diversity
    language_count = len(languages)

    if language_count >= 5:
        score += 20
    elif language_count >= 3:
        score += 15
    elif language_count > 0:
        score += 8

    # README quality
    readme_count = sum(
        1 for r in repos
        if r.get("has_readme", False)
    )

    if repo_count > 0:
        readme_ratio = readme_count / repo_count

        if readme_ratio >= 0.8:
            score += 20
        elif readme_ratio >= 0.5:
            score += 12
        elif readme_ratio >= 0.3:
            score += 6

    # Documentation quality (descriptions)
    documented = 0

    for repo in repos:
        if repo.get("description") and len(repo.get("description", "")) > 10:
            documented += 1

    if repo_count > 0:
        documentation_rate = (documented / repo_count) * 100

        if documentation_rate >= 80:
            score += 15
        elif documentation_rate >= 50:
            score += 10
        elif documentation_rate >= 30:
            score += 5

    # Project activity
    active_repos = sum(
        1 for r in repos
        if r.get("has_activity", False)
    )

    if repo_count > 0:
        active_ratio = active_repos / repo_count

        if active_ratio >= 0.7:
            score += 15
        elif active_ratio >= 0.4:
            score += 8
        elif active_ratio >= 0.2:
            score += 4

    # Community (reduced weight)
    followers = user.get("followers", 0)

    if followers >= 100:
        score += 10
    elif followers >= 20:
        score += 5
    elif followers >= 5:
        score += 2

    # Impact (reduced weight)
    if stars >= 100:
        score += 10
    elif stars >= 50:
        score += 7
    elif stars >= 10:
        score += 4
    elif stars > 0:
        score += 2

    return min(
        score,
        100
    )