from openai import OpenAI
import os
from typing import List
from crewai.tasks.task_output import TaskOutput

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_summary_from_tasks(tasks_output: List[TaskOutput]) -> str:
    combined_output = "\n\n".join(
        f"Agent: {task.agent}\nDescription: {task.description}\nOutput:\n{task.raw}"
        for task in tasks_output
    )

    prompt = f"""
You are an AI assistant summarizing a multi-agent career recommendation report.

Here are the outputs from various agents:
{combined_output}

Summarize this into 5 key insights for a candidate preparing for their job search.
Include strengths, weaknesses, job matches, learning resources, and interview prep tips.
"""

    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
    )

    return response.choices[0].message.content.strip()