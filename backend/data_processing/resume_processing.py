import os
import re
import fitz  # PyMuPDF
import logging
from uuid import uuid4
from dotenv import load_dotenv
from pathlib import Path
from markitdown import MarkItDown
from utils.s3_utils import upload_file_to_s3
from data_processing.skill_matcher import extract_resume_skills_with_openai
import openai

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


def extract_text_from_pdf(file_content: bytes) -> str:
    temp_path = f"temp_resume_{uuid4().hex[:6]}.pdf"
    with open(temp_path, "wb") as f:
        f.write(file_content)

    doc = fitz.open(temp_path)
    raw_text = "\n\n".join(page.get_text("text") for page in doc)
    doc.close()
    os.remove(temp_path)
    return raw_text


def convert_text_to_markdown(text: str, html_path: Path, md_path: Path) -> str:
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(f"<html><body><pre>{text}</pre></body></html>")

    md = MarkItDown()
    result = md.convert(str(html_path))
    markdown = result.text_content

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    return markdown

def extract_name_from_resume(markdown_text: str) -> str:
    """
    Attempts to extract the candidate's name from the beginning of a markdown-formatted resume.
    Heuristic: assumes the name is in the first non-empty line and may begin with a Markdown header (e.g., "# John Doe").

    Args:
        markdown_text (str): Resume content in markdown format.

    Returns:
        str: Extracted name or "Candidate" if not found.
    """
    lines = markdown_text.strip().splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Remove markdown header if present
        if line.startswith("#"):
            line = re.sub(r"^#+\s*", "", line).strip()
        # Check for name-like pattern: two or three capitalized words
        if re.match(r"^[A-Z][a-z]+(\s+[A-Z][a-z]+){1,2}$", line):
            return line
    return "Candidate"

def process_pdf(file_content: bytes, file_name: str) -> dict:
    logging.basicConfig(level=logging.DEBUG)
    try:
        logging.debug("Starting PDF processing using PyMuPDF + MarkItDown.")

        raw_text = extract_text_from_pdf(file_content)

        # Filenames
        pdf_filename = Path(file_name).stem.replace(" ", "_").upper().split('_')[0]
        html_path = Path(f"temp_{uuid4().hex[:6]}.html")
        md_path = Path(f"{pdf_filename}_resume.md")

        # Convert text to markdown via HTML
        markdown_text = convert_text_to_markdown(raw_text, html_path, md_path)
        logging.debug(f"Converted to markdown: {md_path}")

        name = extract_name_from_resume(markdown_text)
        logging.debug(f"Extracted name: {name}")

        # Extract skills
        extracted_skills = extract_resume_skills_with_openai(markdown_text)
        logging.debug(f"Extracted skills: {extracted_skills}")

        # Upload to S3
        markdown_s3_url = upload_file_to_s3(
            file_path=str(md_path),
            source="resumes/markdown",
            metadata={
                "file_type": "markdown",
                "original_filename": file_name
            }
        )
        logging.debug(f"Markdown uploaded to S3: {markdown_s3_url}")

        # Clean up
        os.remove(html_path)
        os.remove(md_path)

        return {
            "candidate_name": name,
            "markdown_s3_url": markdown_s3_url,
            "pdf_filename": pdf_filename,
            "extracted_skills": extracted_skills,
            "status": "success",
            "message": "Resume processed successfully using PyMuPDF + MarkItDown."
        }

    except Exception as e:
        logging.error(f"Error in resume processing: {e}", exc_info=True)
        raise RuntimeError(f"Resume processing failed: {str(e)}")