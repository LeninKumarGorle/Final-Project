from litellm import completion
import os
from dotenv import load_dotenv
from utils.s3_utils import fetch_markdown_from_s3
import requests

load_dotenv()

MODEL_API_KEYS = {
    "gpt-4o": {"model": "gpt-4o", "api_key": os.getenv("OPENAI_API_KEY")},   
    "claude": {"model": "claude-3-5-sonnet-20241022", "api_key": os.getenv("ANTHROPIC_API_KEY")},  
    "grok": {"model": "xai/grok-2-1212", "api_key": os.getenv("GROK_API_KEY")},  
}

def generate_resume_summary(resume_s3_path: str)-> str:
    if resume_s3_path.startswith("s3://"):
        resume_s3_path = "/".join(resume_s3_path.split("/")[3:])
        
    resume_text = fetch_markdown_from_s3(resume_s3_path)

    if not resume_text:
        raise ValueError(f"Could not fetch resume markdown from {resume_s3_path}")
    
    model_id = "grok"
    creds = MODEL_API_KEYS[model_id]
    prompt = f"""
You are an expert resume summarizer. Read the resume text and produce a structured summary in the following format:

**Education**
- ...

**Experience**
- ...

**Skills**
- ...

**Projects**
- ...


Resume:
{resume_text}
    """

    response = completion(
        model=creds["model"],
        api_key=creds["api_key"],
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        temperature=0.3
    )
    print(response)

    return response["choices"][0]["message"]["content"].strip()

