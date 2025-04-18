from litellm import completion
import os
from dotenv import load_dotenv

#from crewai.tasks.task_output import TaskOutput

load_dotenv()

MODEL_API_KEYS = {
    "gpt-4o": {"model": "gpt-4o", "api_key": os.getenv("OPENAI_API_KEY")},   
    "claude": {"model": "claude-3-5-sonnet-20241022", "api_key": os.getenv("ANTHROPIC_API_KEY")},  
    "grok": {"model": "xai/grok-2-1212", "api_key": os.getenv("GROK_API_KEY")},  
}

def generate_next_question(mode, role, previous_question, user_answer, resume_summary=""):
    context = (
        f"You are acting as a professional interviewer for a {role} role. "
        f"This is a {mode.lower()} interview. "
        f"Your goal is to conduct a realistic, structured interview by asking questions that build logically on the candidate's previous response.\n\n"
    )

    if resume_summary and mode.lower() == "resume":
        context += (
            "Here is the summary of the candidate's resume:\n"
            f"{resume_summary}\n\n"
        )

    context += (
        f"Previous Question: {previous_question}\n"
        f"Candidate's Answer: {user_answer}\n\n"
        "Based on this response, ask the next appropriate follow-up question. "
        "Keep it relevant, concise, and focused on assessing behavioral or technical skills depending on the interview mode. "
        "Respond only with the next question — no explanation or comments."
    )

    creds = MODEL_API_KEYS["grok"]
    response = completion(
        model=creds["model"],
        api_key=creds["api_key"],
        messages=[{"role": "user", "content": context}],
        temperature=0.5,
        max_tokens=200
    )
    return response["choices"][0]["message"]["content"].strip()

def evaluate_interview(transcript, role, mode):

    prompt = (
        f"You are acting as a senior interviewer and evaluator reviewing a {mode.lower()} interview for a {role} role.\n"
        "Your task is to review the full transcript below and provide a structured evaluation with:\n"
        "- Strengths (based on responses)\n"
        "- Weaknesses\n"
        "- Suggestions for improvement\n"
        "- Overall readiness level\n"
        "Be clear and concise, and use a professional tone.\n\n"
        "Transcript:\n"
    )

    for i, (q, a) in enumerate(transcript):
        prompt += f"Q{i+1}: {q}\nA{i+1}: {a}\n"

    creds = MODEL_API_KEYS["grok"]
    response = completion(
        model=creds["model"],
        api_key=creds["api_key"],
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=1200
    )
    return response["choices"][0]["message"]["content"].strip()
