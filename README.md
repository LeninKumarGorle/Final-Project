# AI-powered Interview Preparation Assistant

## Team Members
- **Aditi Ashutosh Deodhar**  002279575  
- **Lenin Kumar Gorle**       002803806  
- **Poorvika Girish Babu**    002801388

## Project Overview
### Problem Statement

Job seekers in the tech industry struggle with fragmented and generic interview preparation resources. The lack of personalized guidance tailored to specific roles, companies, and individual resumes leads to inefficient and often ineffective preparation.
Navigating multiple platforms without contextual recommendations creates friction and uncertainty, reducing a candidate’s chances of success.

### Methodology

This project follows a modular and intelligent architecture to deliver a personalized interview preparation experience:

- **Resume and JD Parsing**  
  Uses NLP techniques to extract key entities, skills, and experiences from resumes and job descriptions. This helps align candidate profiles with job expectations.

- **Agent-Based Architecture**
  - **RecommenderAgent**  
    Suggests learning resources and resume improvements based on resume-job match using data from **Snowflake**, **LinkedIn**, and **Coursera**.
  - **MockInterviewAgent**  
    Simulates interviews in **Behavioral**, **Resume-based**, and **Online Assessment (OA)** modes using questions sourced from **LeetScrape**, and provides interactive feedback.
  - **FAQAgent**  
    Answers user questions using **Retrieval-Augmented Generation (RAG)** by querying **Pinecone**, which stores community-sourced interview tips (e.g., Reddit).

- **FastAPI Backend + Streamlit UI**  
  Backend REST APIs handle resume analysis, interview question generation, and query responses. The Streamlit-based UI guides users through uploads, interactions, and evaluations.

- **DBT + Airflow**  
  Handles data scraping (e.g., LinkedIn jobs), transformation, and seeding pipelines to keep structured data consistent and fresh.

- **Evaluation & Reporting**  
  Interview evaluations and resume analysis results are converted to **PDF reports** using markdown-to-PDF logic for user downloads.





### Scope

- Support for multiple technical roles (e.g., Data Scientist, Software Engineer, AI Engineer) and top companies (e.g., MAANG).

- End-to-end experience covering resume parsing, mock interviews, and question answering.

- Integration of structured (Snowflake, LinkedIn) and unstructured (Reddit, LeetScrape) data sources.

- Deployment-ready architecture using Docker, modular agents, and scalable design for adding more domains.

- Limited to English-language resumes and interviews for the initial version, with scope to expand to multilingual support.


## Technologies Used
```
JWT (JSON Web Tokens)
PyMuPDF
Selenium
Leetscrape
CrewAI
Reddit Scraper (asyncpraw)
AWS S3
Snowflake
Pinecone Vector DB
OpenAI
FastAPI
Streamlit

```

## Architecture Diagram
![image](https://github.com/user-attachments/assets/b8c65512-84e6-450c-bab3-3ae965a16feb)


## Agentic Architecture
![image](https://github.com/user-attachments/assets/3c187894-f67f-4261-acad-250c0c5238c9)


## Codelabs Documentation
https://codelabs-preview.appspot.com/?file_id=1aCPKRj-QbRk5n4gkFNslFjnlSHXvKFUo8Fb74Y3V0FI

## Demo
https://shorturl.at/shNyk

## Hosted Applications links 

- Frontend : https://frontend-325254329458.us-central1.run.app
- Backend : [https://backend-487006321216.us-central1.run.app](https://backend-325254329458.us-central1.run.app)

## Prerequisites
```
-Python 3.10+
-Docker installed and running
-Docker Compose installed
-AWS S3 bucket with credentials
-OpenAI API key
-Pinecone API key
-Streamlit installed
-FastAPI framework
-Tavilly API Key
```

## Set Up the Environment
```sh
# Clone the repository
git clone https://github.com/BigDataIA-Spring25-Team-6/Assignment05-Part01.git
cd DAMG7245-Assignment05-Part-01.git

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate     # On Windows
# source venv/bin/activate  # On macOS/Linux

# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables
# Create a .env file with your AWS, Pinecone, and OpenAI credentials

# Run FastAPI backend (inside /api folder)
cd api
uvicorn fastapi_backend:app --host 0.0.0.0 --port 8000 --reload

# Run Streamlit frontend (in a new terminal, inside /frontend folder)
cd ../frontend
streamlit run streamlit_app.py

# Optional: Run using Docker Compose from root directory
docker-compose up --build

```

## Project Structure

```

ASSIGNMENT05-PART-01/

├── api/                 # FastAPI backend
 ├── Dockerfile          # Docker file for backend to build and deploy
 ├── .dockerignore       # Docker ignore file to ignore the unnecessary files          
 ├── requirements.txt    # backend dependencies

├── data_prep/           # Data processing scripts (chunking, RAG)

├── frontend/            # Streamlit frontend
 ├── Dockerfile          # Docker file for frontend to build and deploy
 ├── .dockerignore       # Docker ignore file to ignore the unnecessary files
 ├── requirements.txt    # frontend dependencies

├── .dockerignore        # Docker ignore file

├── .gitignore           # Git ignore file

├── docker-compose.yaml  # Docker file to locally deploy

├── requirements.txt     # Dependencies file

```
