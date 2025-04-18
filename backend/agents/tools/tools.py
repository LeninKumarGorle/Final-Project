from crewai.tools import BaseTool
from openai import OpenAI
from pydantic import BaseModel, Field
import requests
import snowflake.connector
import os
from dotenv import load_dotenv
import ast, contextlib, io
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

# ------------------------- LEETCODE SCRAPE TOOL -------------------------

LEETSERVICE = "http://localhost:8010"

class FetchNextLeetQuestionInput(BaseModel):
    topic: str = Field(..., description="LeetCode topic like array, dp, graph")
    index: int = Field(default=0, description="Index of the question to fetch")

class FetchNextLeetQuestionTool(BaseTool):
    name: str = "fetch_next_leet_question"
    description: str = "Fetch a LeetCode question from leetscrape microservice"
    args_schema: type[BaseModel] = FetchNextLeetQuestionInput

    def _run(self, topic: str, index: int = 0) -> str:
        try:
            res = requests.get(f"{LEETSERVICE}/questions/{topic}")
            print(res.status_code, res.text)
            if res.status_code != 200:
                return f"Failed to fetch questions for topic '{topic}'"

            questions = res.json().get("questions", [])
            print(res.json())
            if not questions or index >= len(questions):
                return f"No questions found for topic '{topic}' at index {index}"

            q = questions[index]
            slug = q["titleSlug"]
            detail = requests.get(f"{LEETSERVICE}/question-detail/{slug}").json()

            return {
                "question_text": (
                    f"### {detail.get('title', 'Unknown')} ({detail.get('difficulty', '')})\n\n"
                    f"https://leetcode.com/problems/{slug}/\n\n"
                    f"**Topics:** {', '.join(detail.get('topics', []))}\n\n"
                    f"{detail.get('description', 'No description available.')}"
                ),
                "code_stub": detail.get("code_stub", "# Starter code not available.")
            }
        except Exception as e:
            return f"Error fetching question: {str(e)}"

# ------------------------- CODE FEEDBACK TOOL -------------------------

class CodeFeedbackInput(BaseModel):
    problem: str = Field(..., description="Problem description")
    code: str = Field(..., description="Python code string")

class CodeFeedbackTool(BaseTool):
    name: str = "get_code_feedback"
    description: str = "Feedback on submitted code"
    args_schema: type[BaseModel] = CodeFeedbackInput

    def _run(self, problem: str, code: str) -> str:
        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        prompt = f"""
You are a coding interview assistant.

Evaluate the following code based on this problem statement:

---
PROBLEM:
{problem}

CODE:
```python
{code}
```

1. Does the code correctly solve the problem? Justify your answer.
2. What is the time complexity? Explain how you derived it.
3. What is the space complexity? Explain why.
4. Suggest improvements or optimizations if any.

Return your answer in a clear, structured markdown format.
"""

        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )

        return response.choices[0].message.content.strip()
    
# ------------------------- REDDIT INTERVIEW TIPS TOOL -------------------------
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import os
from utils.pinecone_query import query_pinecone_chunks 

# Define input schema for the tool
class FetchRelevantChunksInput(BaseModel):
    query: str = Field(..., description="Query to search relevant Reddit chunks")
    role: str = Field(None, description="Optional job role filter")
    company: str = Field(None, description="Optional company filter")

# Tool definition
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
                    f"🔹 Title: {metadata.get('title')}\n"
                    f"📌 Subreddit: {metadata.get('subreddit')}\n"
                    f"🧠 Chunk: {metadata.get('text')[:300]}...\n"
                    f"🔗 Link: {metadata.get('permalink')}\n\n"
                )

            return response.strip()

        except Exception as e:
            return f"Error fetching chunks from Pinecone: {str(e)}"