from crewai import Agent
from agents.tools.tools import FetchRelevantChunksFromPineconeTool

faq_agent = Agent(
    role="FAQ Assistant",
    goal="Answer interview-related questions using Reddit discussions stored in Pinecone",
    backstory=(
        "You are a helpful assistant trained on Reddit discussions to provide practical advice and answers to career-related "
        "questions. You fetch the most relevant community insights using semantic search from a Pinecone vector database."
    ),
    tools=[
        FetchRelevantChunksFromPineconeTool()
    ],
    verbose=True,
)