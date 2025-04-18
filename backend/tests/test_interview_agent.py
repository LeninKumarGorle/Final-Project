from agents.crew_config import orchestrator_agent
from unittest.mock import patch

def test_orchestrator_agent_question_generation():
    with patch("agents.tools.tools.QuestionGenerationTool._run") as mock_run:
        mock_run.return_value = "What is your experience with microservices?"
        response = orchestrator_agent.run("next_question")
        assert isinstance(response, str)
        assert "experience" in response.lower()

def test_orchestrator_agent_interview_evaluation():
    with patch("agents.tools.tools.InterviewEvaluationTool._run") as mock_run:
        mock_run.return_value = "Candidate demonstrated a strong grasp of backend systems."
        response = orchestrator_agent.run("evaluate")
        assert isinstance(response, str)
        assert "candidate" in response.lower()