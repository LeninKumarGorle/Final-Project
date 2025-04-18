from crewai import Agent
from agents.tools.tools import FetchNextLeetQuestionTool, CodeFeedbackTool

oa_leetscrape_agent = Agent(
    role="OA Interview Assistant",
    goal="Guide the user through one coding question at a time with feedback",
    backstory=(
        "You are an interactive coding mentor trained to help candidates solve OA-style questions one-by-one. "
        "You pick a question from a topic, evaluate the candidate's solution, and give helpful feedback including complexity."
    ),
    tools=[FetchNextLeetQuestionTool(), CodeFeedbackTool()],
    verbose=True
)