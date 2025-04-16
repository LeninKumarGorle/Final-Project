from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import requests
import snowflake.connector
import os
from dotenv import load_dotenv
import ast, contextlib, io

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