from crewai import Agent
from agents.tools.tools import FetchMatchingJobsTool, FetchRelevantCoursesTool, WebSearchTool

recommender_agent = Agent(
    role="Recommender",
    goal="Suggest the most relevant learning resources based on user's skill gap and job role",
    backstory=(
        "You are a personalized recommendation assistant trained to identify gaps between a user's resume and job requirements "
        "and suggest highly rated Coursera courses and job leads from LinkedIn to help bridge the gap."
    ),
    tools=[
        FetchRelevantCoursesTool(),
        FetchMatchingJobsTool(),
        WebSearchTool()    
    ],
    verbose=True,
)