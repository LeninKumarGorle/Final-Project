# import sys
# import os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse
from agents.crew_config import run_recommendation_pipeline
from utils.pdf_utils import generate_pdf_report_with_details
import io

app = FastAPI()

@app.post("/analyze-resume/")
async def analyze_resume(
    file: UploadFile,
    job_description: str = Form(...),
    location: str = Form(...)
):
    file_content = await file.read()

    result = run_recommendation_pipeline(
        file_content=file_content,
        file_name=file.filename,
        job_description=job_description,
        location=location
    )

    full_text = result["recommendation_report"].raw
    summary = result["summary"]
    candidate_name = result["candidate_name"]
    match_result = {
        "resume_skills": result["resume_skills"],
        "jd_skills": result["jd_skills"],
        "matched_skills": result["matched_skills"],
        "missing_skills": result["missing_skills"],
        "match_score": result["match_score"]
    }

    # Generate enhanced PDF report in memory
    pdf_buffer = io.BytesIO()
    generate_pdf_report_with_details(candidate_name, match_result, full_text, output_stream=pdf_buffer)
    pdf_bytes = pdf_buffer.getvalue()

    return JSONResponse(content={
        "summary": summary,
        "pdf_base64": pdf_bytes.decode("latin1")
    })