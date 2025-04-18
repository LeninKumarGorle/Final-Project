from crewai import Crew, Task
from agents.recommender_agent import recommender_agent
from agents.summary_generator import generate_summary_from_tasks
from data_processing.resume_processing import process_pdf
from data_processing.skill_matcher import extract_jd_skills_with_openai, compare_skills
from dotenv import load_dotenv

from agents.tools.tools import CodeFeedbackInput, CodeFeedbackTool, FetchNextLeetQuestionInput, FetchNextLeetQuestionTool
from agents.leetscrape_agent import oa_leetscrape_agent
from agents.faq_agent import faq_agent

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

def run_oa_session(user_input: str, code: str = None, problem: str = None, state: dict = None):
    session_state = state or {}

    # Step 1: New session or topic restart → force reset and return first question
    if user_input.lower() in [
        "array", "string", "dp", "graph", "tree", "stack", "queue",
        "hash-table", "greedy", "two-pointers", "sliding-window", "linked-list"]:

        session_state["topic"] = user_input.lower()
        session_state["index"] = 0
        session_state["state"] = "waiting_for_code"
        session_state["skipped"] = []

        tool = FetchNextLeetQuestionTool()
        input_data = FetchNextLeetQuestionInput(topic=session_state["topic"])
        q = tool._run(**input_data.model_dump())

        question_text = q.get("question_text") if isinstance(q, dict) else str(q)
        code_stub = q.get("code_stub") if isinstance(q, dict) else ""

        return {
            "question_text": question_text,
            "code_stub": code_stub,
            "session_state": session_state
        }
    
    elif code and session_state.get("topic") and session_state.get("index") is not None:
        session_state["state"] = "waiting_for_next"

        problem = problem or "Problem not provided"
        print(problem,"Here\n\n\n")

        tool = CodeFeedbackTool()
        input_data = CodeFeedbackInput(problem=problem, code=code)
        feedback = tool._run(**input_data.model_dump())

        return {
            "question_text": feedback + "\n\n Type 'next' to try another question.",
            "code_stub": code,
            "session_state": session_state
        }
    
    elif user_input.strip().lower() == "next":
        if session_state.get("state") == "waiting_for_code":
            session_state.setdefault("skipped", []).append(session_state.get("index", 0))

        session_state["index"] = session_state.get("index", 0) + 1
        session_state["state"] = "waiting_for_code"

        tool = FetchNextLeetQuestionTool()
        input_data = FetchNextLeetQuestionInput(
            topic=session_state["topic"],
            index=session_state["index"]
        )
        q = tool._run(**input_data.model_dump())

        question_text = q.get("question_text") if isinstance(q, dict) else str(q)
        code_stub = q.get("code_stub") if isinstance(q, dict) else ""

        return {
            "question_text": question_text,
            "code_stub": code_stub,
            "session_state": session_state
        }
    else:
        return {
            "question_text": "Please provide a code answer or type 'next' for another question.",
            "code_stub": "",
            "session_state": session_state
        }
    
def run_faq_pipeline(faq_query: str, job_role: str = None, company: str = None):
    try:
        # Step 1: Define the agent's task using the user's query
        task = Task(
            description=(
                f"You are an interview assistant. Your task is to search Reddit discussion data "
                f"for helpful answers to the following question:\n\n"
                f"'{faq_query}'\n\n"
                f"Use the semantic search tool to find community advice from Reddit chunks stored in Pinecone."
                + (f"\nFilter your results by job role: {job_role}." if job_role else "")
                + (f"\nFilter your results by company: {company}." if company else "")
                + "\nFormat your output as an answer followed by 2–5 relevant Reddit links."
            ),
            expected_output="Helpful response to the user's question with links to relevant Reddit discussions.",
            agent=faq_agent
        )

        # Step 2: Assemble the crew and run the task
        crew = Crew(
            agents=[faq_agent],
            tasks=[task],
            verbose=True
        )

        final_output = crew.kickoff()

        # Step 3 (Optional): Summarize if needed
        #summary = generate_summary_from_tasks(final_output.tasks_output)

        return {
            "faq_query": faq_query,
            "job_role": job_role,
            "company": company,
            "faq_response": final_output,
            #"summary": summary
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
