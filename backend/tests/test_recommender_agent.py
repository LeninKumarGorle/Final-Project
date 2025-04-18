from agents.crew_config import recommender_agent
from unittest.mock import patch

def test_recommender_agent_relevant_courses():
    with patch("agents.tools.tools.FetchRelevantCoursesTool._run") as mock_run:
        mock_run.return_value = "Recommended: 'Advanced SQL for Data Analysts'."
        response = recommender_agent.run("recommend_courses")
        assert isinstance(response, str)
        assert "recommended" in response.lower()

def test_recommender_agent_matching_jobs():
    with patch("agents.tools.tools.FetchMatchingJobsTool._run") as mock_run:
        mock_run.return_value = "Found 5 matching jobs on LinkedIn."
        response = recommender_agent.run("recommend_jobs")
        assert isinstance(response, str)
        assert "jobs" in response.lower()

def test_recommender_agent_web_search():
    with patch("agents.tools.tools.WebSearchTool._run") as mock_run:
        mock_run.return_value = "Check out these articles on Kubernetes from Medium and Dev.to."
        response = recommender_agent.run("search_resources")
        assert isinstance(response, str)
        assert "kubernetes" in response.lower() or "article" in response.lower()
