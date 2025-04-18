from crewai import Agent
from agents.tools.tools import QuestionGenerationTool, InterviewEvaluationTool

orchestrator_agent = Agent(
    role="Interview Orchestrator",
    goal="Route the interview flow to the right tool based on user intent",
    backstory="You manage the flow of a mock interview. Based on the interview stage, you decide whether to continue with follow-up questions or to evaluate the session.",
    tools=[
        QuestionGenerationTool(), 
        InterviewEvaluationTool()
    ],
    verbose=True
)