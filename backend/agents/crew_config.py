from crewai import Crew, Task
from agents.interview_agent import orchestrator_agent
from dotenv import load_dotenv
from typing import List, Tuple, Literal
from pprint import pprint
from agents.recommender_agent import recommender_agent
from agents.summary_generator import generate_summary_from_tasks
from data_processing.resume_processing import process_pdf
from data_processing.skill_matcher import extract_jd_skills_with_openai, compare_skills

from agents.tools.tools import CodeFeedbackInput, CodeFeedbackTool, FetchNextLeetQuestionInput, FetchNextLeetQuestionTool
from agents.leetscrape_agent import oa_leetscrape_agent


load_dotenv()

session_state = {}

def run_interview_orchestration_pipeline(
    action: Literal["next_question", "evaluate"],
    role: str,
    mode: str,
    previous_question: str = "",
    user_answer: str = "",
    resume_summary: str = "",
    transcript: List[Tuple[str, str]] = []
) -> str:
    """
    A unified hierarchical CrewAI pipeline for handling both next question generation
    and interview evaluation based on user-provided action.
    """
    context_blob = f"""
ROLE CONTEXT (DO NOT TREAT AS SUBTASK)

You are managing a mock interview for role: {role}, mode: {mode}.
The user action is: {action}

INSTRUCTIONS:

- If action is "next_question", you MUST use tool `generate_followup_question` with:
  - role, mode, previous_question, user_answer, resume_summary (optional)

- If action is "evaluate", you MUST use tool `evaluate_interview` with:
  - transcript, role, mode

IMPORTANT RULES:

1. Only use ONE tool based on the action.
2. Do NOT repeat tool calls with the same input.
3. Once you get a valid response from a tool, IMMEDIATELY stop and return it as your final answer.
4. Do NOT attempt to simulate or guess the tool output — you must invoke the real tool.

The agent has access to these fields:
{{
  role: {role}
  mode: {mode}
  action: {action}
  previous_question: {previous_question}
  user_answer: {user_answer}
  resume_summary: {resume_summary}
  transcript: {transcript[:1]}...
}}

Now, proceed carefully and call only the correct tool.
"""
    normalized_transcript = [tuple(pair) for pair in transcript]
    task = Task(
        description=context_blob.strip(),
        expected_output="The next follow-up question or the structured interview evaluation report.",
        agent=orchestrator_agent,
        input={  
            "action": action,
            "role": role,
            "mode": mode,
            "previous_question": previous_question,
            "user_answer": user_answer,
            "resume_summary": resume_summary,
            "transcript": normalized_transcript
        }
    )

    crew = Crew(
        agents=[orchestrator_agent],
        tasks=[task],
        verbose=True
    )
    print("FINAL CONTEXT PASSED TO CREW ")
    print("DEBUG: after task type(task.context):", type(task.context))
    print("DEBUG: after task task.context:", task.context)
    print("DEBUG: BEFORE kickoff context:")
    result = crew.kickoff()
    print("DEBUG: AFTER kickoff context:")
    raw_output = result.tasks_output[0]
    final_output = raw_output.output if hasattr(raw_output, "output") else raw_output
    return result.tasks_output[0].raw



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