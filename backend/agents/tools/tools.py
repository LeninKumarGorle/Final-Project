from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import requests
import snowflake.connector
import os
from dotenv import load_dotenv
import ast, contextlib, io
from litellm import completion
from typing import List, Tuple
from utils.pinecone_query import query_pinecone_chunks

load_dotenv()

# ------------------------- COURSE TOOL -------------------------

class FetchRelevantCoursesInput(BaseModel):
    skill: str = Field(..., description="Skill to search courses for")
    job_role: str = Field(..., description="Target job role")

class FetchRelevantCoursesTool(BaseTool):
    name: str = "fetch_relevant_courses"
    description: str = "Fetch Coursera courses based on skill and job role"
    args_schema: type[BaseModel] = FetchRelevantCoursesInput


    def _run(self, skill: str, job_role: str) -> str:
        try:
            conn = snowflake.connector.connect(
                user=os.getenv("SNOWFLAKE_USER"),
                password=os.getenv("SNOWFLAKE_PASSWORD"),
                account=os.getenv("SNOWFLAKE_ACCOUNT"),
                warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
                database="FINAL_PROJECT",
                schema="DATA_STORE",
                role=os.getenv("SNOWFLAKE_ROLE"),
            )
            cursor = conn.cursor()

            top_skills = [s.strip() for s in skill.split(",")][:3]
            skill_conditions = " OR ".join([
                f"(TITLE ILIKE '%{s}%' OR SKILLS ILIKE '%{s}%')" for s in top_skills
            ])

            query = f"""
                SELECT TITLE, URL, RATING
                FROM COURSES_CLEANED
                WHERE JOB_ROLE ILIKE '%{job_role}%'
                AND ({skill_conditions})
                ORDER BY RATING DESC
                LIMIT 5;
            """
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            conn.close()

            if not results:
                return f"No Coursera courses found for top skills: {', '.join(top_skills)}."

            return "\n".join([
                f"{row[0]} ({row[2]}/5): {row[1]}" for row in results
            ])
        except Exception as e:
            return f"Error fetching Coursera courses: {str(e)}"

# ------------------------- JOB TOOL -------------------------

class FetchMatchingJobsInput(BaseModel):
    job_role: str = Field(..., description="Job title or role to search for")
    skills: list[str] = Field(default=[], description="Skills to match job descriptions")

class FetchMatchingJobsTool(BaseTool):
    name: str = "fetch_matching_jobs"
    description: str = "Fetch LinkedIn jobs from Snowflake based on job role"
    args_schema: type[BaseModel] = FetchMatchingJobsInput

    def _run(self, job_role: str, skills: list[str] = None) -> str:
        try:
            conn = snowflake.connector.connect(
                user=os.getenv("SNOWFLAKE_USER"),
                password=os.getenv("SNOWFLAKE_PASSWORD"),
                account=os.getenv("SNOWFLAKE_ACCOUNT"),
                warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
                database="FINAL_PROJECT",
                schema="DATA_STORE",
                role=os.getenv("SNOWFLAKE_ROLE"),
            )
            cursor = conn.cursor()

            # Build a flexible WHERE clause using job_role and skill matches
            conditions = [f"ROLE ILIKE '%{job_role}%'"]
            if skills:
                skill_conditions = [f"DESCRIPTION ILIKE '%{s}%'" for s in skills]
                conditions.append(f"({' OR '.join(skill_conditions)})")

            query = f"""
                SELECT JOB_TITLE, COMPANY_NAME, LOCATION, JOB_URL
                FROM CLEANED_LINKEDIN_JOBS
                WHERE {' AND '.join(conditions)}
                LIMIT 5;
            """

            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            conn.close()

            if not results:
                return f"No job listings found for role '{job_role}' with related skills."

            return "\n".join([f"{title} at {company} ({loc}): {url}" for title, company, loc, url in results])
        except Exception as e:
            return f"Error fetching job listings: {str(e)}"

        
# ------------------------- WEB SEARCH TOOL -------------------------

class WebSearchInput(BaseModel):
    query: str = Field(..., description="Focused search query like 'interview tips for Data Analyst using Python'")

class WebSearchTool(BaseTool):
    name: str = "web_search_tool"
    description: str = "Fetch relevant career prep resources using Tavily search"
    args_schema: type = WebSearchInput

    def _run(self, query: str) -> str:
        try:
            tavily_key = os.getenv("TAVILY_API_KEY")
            response = requests.post(
                "https://api.tavily.com/search",
                headers={"Authorization": f"Bearer {tavily_key}"},
                json={"query": query, "num_results": 5}
            )
            results = response.json().get("results", [])
            if not results:
                return "No useful resources found from Tavily."
            return "\n".join([f"{r['title']}: {r['url']}" for r in results])
        except Exception as e:
            return f"Tavily search failed: {str(e)}"

class QuestionGenerationInput(BaseModel):
    mode: str = Field(..., description="Interview mode (e.g., Resume, Behavioral, Technical)")
    role: str = Field(..., description="Target job role")
    previous_question: str = Field(..., description="Last question asked during the interview")
    user_answer: str = Field(..., description="Candidate's response to the previous question")
    resume_summary: str = Field("", description="Optional resume summary for context in resume-based interviews")

class QuestionGenerationTool(BaseTool):
    name: str = "generate_followup_question"
    description: str = "Generates the next interview question based on previous interaction"
    args_schema: type = QuestionGenerationInput

    def _run(self, mode: str, role: str, previous_question: str, user_answer: str, resume_summary: str = "") -> str:
        try:
            creds = {
                "model": "xai/grok-2-1212",
                "api_key": os.getenv("GROK_API_KEY")
            }

            context = (
                f"You are acting as a professional interviewer for a {role} role. "
                f"This is a {mode.lower()} interview. "
                f"Your goal is to conduct a realistic, structured interview by asking questions that build logically on the candidate's previous response.\n\n"
            )

            if resume_summary and mode.lower() == "resume":
                context += f"Here is the summary of the candidate's resume:\n{resume_summary}\n\n"

            context += (
                f"Previous Question: {previous_question}\n"
                f"Candidate's Answer: {user_answer}\n\n"
                "Based on this response, ask the next appropriate follow-up question. "
                "Keep it relevant, concise, and focused on assessing behavioral or technical skills depending on the interview mode. "
                "Respond only with the next question — no explanation or comments."
            )

            response = completion(
                model=creds["model"],
                api_key=creds["api_key"],
                messages=[{"role": "user", "content": context}],
                temperature=0.5,
                max_tokens=200
            )
            return response["choices"][0]["message"]["content"].strip()

        except Exception as e:
            return f"Error generating follow-up question: {str(e)}"

class InterviewEvaluationInput(BaseModel):
    transcript: List[Tuple[str, str]] = Field(..., description="List of (question, answer) tuples from the interview")
    role: str = Field(..., description="Target job role")
    mode: str = Field(..., description="Type of interview (e.g., Resume, Technical, Behavioral)")

class InterviewEvaluationTool(BaseTool):
    name: str = "evaluate_interview"
    description: str = "Evaluates an interview transcript and provides structured feedback"
    args_schema: type = InterviewEvaluationInput

    def _run(self, transcript: List[Tuple[str, str]], role: str, mode: str) -> str:
        try:
            transcript = [tuple(pair) for pair in transcript if isinstance(pair, (list, tuple)) and len(pair) == 2]
            creds = {
                "model": "xai/grok-2-1212",
                "api_key": os.getenv("GROK_API_KEY")
            }

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

            response = completion(
                model=creds["model"],
                api_key=creds["api_key"],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=1200
            )
            return response["choices"][0]["message"]["content"].strip()

        except Exception as e:
            return f"Error evaluating interview: {str(e)}"

class FetchRelevantChunksInput(BaseModel):
    query: str = Field(..., description="Query to search relevant Reddit chunks")
    role: str = Field(None, description="Optional job role filter")
    company: str = Field(None, description="Optional company filter")

class FetchRelevantChunksFromPineconeTool(BaseTool):
    name: str = "fetch_relevant_chunks"
    description: str = "Fetch relevant Reddit discussion chunks from Pinecone using semantic search and optional filters"
    args_schema: type = FetchRelevantChunksInput

    def _run(self, query: str, role: str = None, company: str = None) -> str:
        try:
            results = query_pinecone_chunks(
                query=query,
                role=role,
                company=company,
                api_key=os.getenv("PINECONE_API_KEY"),
                index_name=os.getenv("INDEX_NAME"),
                top_k=5
            )

            if results.get("status") == "error" or not results.get("matches"):
                return results.get("message", f"No relevant chunks found for query '{query}'.")
                #return f"No relevant chunks found for query '{query}'."

            response = ""
            for match in results["matches"]:
                metadata = match.get("metadata", {})
                response += (
                    f"Title: {metadata.get('title')}\n"
                    f"Subreddit: {metadata.get('subreddit')}\n"
                    f"Chunk: {metadata.get('text')[:300]}...\n"
                    f"Link: {metadata.get('permalink')}\n\n"
                )

            return response.strip()

        except Exception as e:
            return f"Error fetching chunks from Pinecone: {str(e)}"
