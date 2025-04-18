from agents.crew_config import run_faq_pipeline
 
def test_agent_with_valid_query():
    query = "What are common interview questions for backend engineers?"
    result = run_faq_pipeline(
        faq_query=query,
        job_role="Backend Developer",
        company="Google"
    )
 
    # Check if result is the new CrewOutput object
    if hasattr(result, "raw"):
        raw_output = result.raw
        assert isinstance(raw_output, str)
        assert "unfortunately" in raw_output.lower() or "interview" in raw_output.lower()
    else:
        # legacy fallback if it's dict-based
        assert isinstance(result, dict)
        assert "faq_response" in result
 
 
def test_agent_with_irrelevant_query():
    query = "Why is the sky blue?"
    result = run_faq_pipeline(
        faq_query=query,
        job_role="Backend Developer",
        company="Google"
    )
 
    if isinstance(result, dict) and "faq_response" in result:
        raw_output = getattr(result["faq_response"], "raw", "")
        assert "no relevant" in raw_output.lower() or "not relevant" in raw_output.lower()
 
    else:
        raise AssertionError("faq_response not found in result or result format unexpected.")