import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

# --- JD Skill Extraction ---

def extract_jd_skills_with_openai(jd_text: str) -> list:
    prompt = f"""
Extract the technical skills, tools, or platforms required in this job description.
Return them as a comma-separated list.

JD:
{jd_text}
"""
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    skills = response.choices[0].message.content.strip()
    return [s.strip() for s in skills.split(",") if s.strip()]


# --- Resume Skill Extraction ---

def extract_resume_skills_with_openai(markdown: str) -> list:
    prompt = f"""
You are an AI assistant for resume analysis.

Given the following Markdown content extracted from a resume, extract all technical skills, tools, libraries, programming languages, cloud platforms, or frameworks mentioned.

Return them as a clean, comma-separated list.

Markdown:
{markdown}
"""
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    content = response.choices[0].message.content.strip()
    return [s.strip() for s in content.split(",") if s.strip()]


# --- Skill Matching ---

def compare_skills(resume_skills: list, jd_skills: list) -> dict:
    matched = list(set(resume_skills) & set(jd_skills))
    missing = list(set(jd_skills) - set(resume_skills))
    score = round(len(matched) / max(len(jd_skills), 1), 2)

    return {
        "resume_skills": resume_skills,
        "jd_skills": jd_skills,
        "match_score": score,
        "matched_skills": matched,
        "missing_skills": missing,
        "prompt_context": (
            f"Candidate has skills: {', '.join(resume_skills)}.\n"
            f"JD requires: {', '.join(jd_skills)}.\n"
            f"Matched: {', '.join(matched)}.\n"
            f"Missing: {', '.join(missing)}.\n"
            f"Score: {score * 100:.0f}%."
        )
    }