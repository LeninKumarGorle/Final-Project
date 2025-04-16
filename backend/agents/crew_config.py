from crewai import Crew, Task
from agents.recommender_agent import recommender_agent
from agents.summary_generator import generate_summary_from_tasks
from data_processing.resume_processing import process_pdf
from data_processing.skill_matcher import extract_jd_skills_with_openai, compare_skills
from dotenv import load_dotenv

load_dotenv()

session_state = {}

def run_recommendation_pipeline(file_content: bytes, file_name: str, job_description: str, location: str):
    try:
        # Step 1: Extract resume skills
        resume_result = process_pdf(file_content, file_name)
        resume_skills = resume_result["extracted_skills"]

        # Step 2: Extract JD skills
        jd_skills = extract_jd_skills_with_openai(job_description)

        # Step 3: Match skills and get prompt context
        match_result = compare_skills(resume_skills, jd_skills)
        prompt_context = match_result["prompt_context"]

        # Step 4: Define the agent's task
        task = Task(
            description=(
                f"You are an intelligent recommender system.\n\n"
                f"{prompt_context}\n\n"
                f"Use tools to:\n"
                f"1. Recommend Coursera courses based on the top 3 missing skills.\n"
                f"2. Find job listings using the candidate's skills and the target job role as filters. \n"
                f"3. Search the web for interview tips or learning resources for the missing skills.\n\n"
                f"Output a final recommendation report with sections for strengths, weaknesses, job matches, and upskilling suggestions."
            ),
            expected_output="Structured career prep report for the candidate.",
            agent=recommender_agent
        )

        # Step 5: Assemble the crew and run it
        crew = Crew(
            agents=[recommender_agent],
            tasks=[task],
            verbose=True
        )

        final_report = crew.kickoff()

        summary = generate_summary_from_tasks(final_report.tasks_output)

        return {
            "resume_skills": resume_skills,
            "jd_skills": jd_skills,
            "match_score": match_result["match_score"],
            "matched_skills": match_result["matched_skills"],
            "missing_skills": match_result["missing_skills"],
            "markdown_s3_url": resume_result["markdown_s3_url"],
            "recommendation_report": final_report,
            "summary": summary,
            "candidate_name": resume_result.get("candidate_name", "Candidate"),
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }