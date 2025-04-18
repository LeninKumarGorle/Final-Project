from crewai import Crew, Task
from agents.interview_agent import orchestrator_agent
from dotenv import load_dotenv
from typing import List, Tuple, Literal
from pprint import pprint


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