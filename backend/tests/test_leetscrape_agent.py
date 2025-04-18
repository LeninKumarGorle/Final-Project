from agents.crew_config import oa_leetscrape_agent
from unittest.mock import patch

def test_oa_agent_fetch_next_question():
    with patch("agents.tools.tools.FetchNextLeetQuestionTool._run") as mock_run:
        mock_run.return_value = "Please solve the Two Sum problem."
        response = oa_leetscrape_agent.run("next_question")
        assert isinstance(response, str)
        assert "sum" in response.lower()

def test_oa_agent_code_feedback():
    with patch("agents.tools.tools.CodeFeedbackTool._run") as mock_run:
        mock_run.return_value = "Your code passes all test cases with O(n) complexity."
        response = oa_leetscrape_agent.run("evaluate")
        assert isinstance(response, str)
        assert "complexity" in response.lower()