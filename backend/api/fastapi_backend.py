from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from utils.interview_helpers import generate_next_question, evaluate_interview
from utils.resume_summarizer import generate_resume_summary
from agents.crew_config import run_interview_orchestration_pipeline, run_oa_session, run_recommendation_pipeline
from utils.pdf_utils import generate_pdf_report_with_details
import io
from typing import Optional, List, Tuple
import traceback

app = FastAPI()

# Allow CORS for all origins (you can restrict this to specific origins if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class OASessionRequest(BaseModel):
    user_input: str
    code: str | None = None
    problem: str | None = None
    session_state: dict = {}

class QuestionInput(BaseModel):
    mode: str
    role: str
    previous_question: str
    user_answer: str
    resume_s3_path: Optional[str] | None = None

class EvaluationInput(BaseModel):
    transcript: list[tuple[str, str]]
    role: str
    mode: str

@app.post("/oa-session")
def oa_session(request: OASessionRequest):
    print("USER INPUT:", request.user_input)
    print("SESSION STATE:", request.session_state)
    print("CODE:", request.code)

    response = run_oa_session(
        user_input=request.user_input,
        code=request.code,
        problem=request.problem,
        state=request.session_state
    )

    print("RETURNING:", response)
    return JSONResponse(content=response)

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

@app.post("/generate_next_question/")
def ask_next(payload:QuestionInput):
    print(f"mode selected is {payload.mode}")
    resume_summary = ""
    if payload.mode == "Resume":
        resume_summary = generate_resume_summary(payload.resume_s3_path)
    
    
    next_question = generate_next_question(
        mode=payload.mode,
        role=payload.role,
        previous_question=payload.previous_question,
        user_answer=payload.user_answer,
        resume_summary=resume_summary
    )

    return {
        "next_question": next_question
    }


@app.post("/evaluate_interview/")
def evaluate(payload:EvaluationInput):
    evaluation_report = evaluate_interview(
        transcript=payload.transcript,
        role=payload.role,
        mode=payload.mode
    )

    return {
        "evaluation_report": evaluation_report
    }

@app.post("/generates_next_question/")
def ask_next_question(payload: QuestionInput):
    try:
        resume_summary = ""
        if payload.mode.lower() == "resume":
            if not payload.resume_s3_path:
                raise HTTPException(status_code=400, detail="Resume S3 path required for Resume mode")
            resume_summary = generate_resume_summary(payload.resume_s3_path)
        print("running interview orchestration pipeline")
        print(payload)
        result = run_interview_orchestration_pipeline(
            action="next_question",
            role=payload.role,
            mode=payload.mode,
            previous_question=payload.previous_question,
            user_answer=payload.user_answer,
            resume_summary=resume_summary,
            transcript=[]
        )
        print(f"Next question generated: {result}")
        print("TYPE OF RESULT:", type(result))
        return {"next_question": result}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/evaluates_interview/")
def evaluate_interview(payload: EvaluationInput):
    try:
        print(payload)
        result = run_interview_orchestration_pipeline(
            action="evaluate",
            role=payload.role,
            mode=payload.mode,
            transcript=payload.transcript
        )

        return {"evaluation_report": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))