import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from api.fastapi_backend import app

client = TestClient(app)

@patch("your_module.run_oa_session")
def test_oa_session(mock_oa):
    mock_oa.return_value = {"response": "ok"}
    payload = {
        "user_input": "hello",
        "code": "print('hi')",
        "problem": "Two Sum",
        "session_state": {}
    }
    res = client.post("/oa-session/", json=payload)
    assert res.status_code == 200
    assert res.json()["response"] == "ok"

@patch("your_module.run_recommendation_pipeline")
@patch("your_module.generate_pdf_report_with_details")
def test_analyze_resume(mock_pdf, mock_pipeline):
    mock_pipeline.return_value = {
        "summary": "Summary here",
        "candidate_name": "John",
        "resume_skills": ["Python"],
        "jd_skills": ["Python", "SQL"],
        "matched_skills": ["Python"],
        "missing_skills": ["SQL"],
        "match_score": 80,
        "recommendation_report": type("Rec", (), {"raw": "Report content"})
    }
    mock_pdf.return_value = None

    file = ("resume.pdf", b"fake content", "application/pdf")
    data = {"job_description": "Job desc", "location": "CA"}
    res = client.post("/analyze-resume/", files={"file": file}, data=data)

    assert res.status_code == 200
    assert "summary" in res.json()
    assert "pdf_base64" in res.json()

@patch("your_module.run_faq_pipeline")
def test_faq_success(mock_faq):
    mock_faq.return_value = {"status": "success", "answer": "sample"}
    payload = {"query": "What is CI?", "role": "DevOps", "company": "Google"}

    res = client.post("/faq", json=payload)
    assert res.status_code == 200
    assert res.json()["status"] == "success"

@patch("your_module.run_faq_pipeline")
def test_faq_failure(mock_faq):
    mock_faq.return_value = {"status": "error", "message": "Failed"}
    payload = {"query": "What is CI?", "role": "DevOps", "company": "Google"}

    res = client.post("/faq", json=payload)
    assert res.status_code == 400

@patch("your_module.generate_next_question")
@patch("your_module.generate_resume_summary")
def test_generate_next_question_resume_mode(mock_summary, mock_next):
    mock_summary.return_value = "Resume Summary"
    mock_next.return_value = "What is Docker?"

    payload = {
        "mode": "Resume",
        "role": "DevOps",
        "previous_question": "What is CI/CD?",
        "user_answer": "CI means...",
        "resume_s3_path": "resume/path.md"
    }

    res = client.post("/generate_next_question/", json=payload)
    assert res.status_code == 200
    assert res.json()["next_question"] == "What is Docker?"

@patch("your_module.evaluate_interview")
def test_evaluate_interview(mock_eval):
    mock_eval.return_value = "Strong candidate"

    payload = {
        "transcript": [["Q1", "A1"], ["Q2", "A2"]],
        "role": "Backend Engineer",
        "mode": "Role-Based"
    }

    res = client.post("/evaluate_interview/", json=payload)
    assert res.status_code == 200
    assert "evaluation_report" in res.json()

@patch("your_module.run_interview_orchestration_pipeline")
@patch("your_module.generate_resume_summary")
def test_generates_next_question_resume_mode(mock_summary, mock_pipeline):
    mock_summary.return_value = "Summary"
    mock_pipeline.return_value = "What is system design?"

    payload = {
        "mode": "Resume",
        "role": "SWE",
        "previous_question": "Tell me about yourself",
        "user_answer": "I'm a backend engineer",
        "resume_s3_path": "s3/resume.pdf"
    }

    res = client.post("/generates_next_question/", json=payload)
    assert res.status_code == 200
    assert "next_question" in res.json()