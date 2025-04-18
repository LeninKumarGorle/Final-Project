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

- Frontend : https://interview-preparation-app.streamlit.app/
- Backend : https://ai-interview-prep-app-155853387274.us-central1.run.app
- leetscrape microservice: https://leetscrape-155853387274.us-central1.run.app

## Prerequisites
```
- Python 3.10+
- Docker installed and running
- Docker Compose installed
- AWS S3 bucket with credentials (Access Key & Secret Key)
- Snowflake account with database/schema/role access
- OpenAI API key
- Pinecone API key and index set up
- Streamlit installed (pip install streamlit)
- FastAPI framework (pip install fastapi uvicorn)
- Reddit API credentials for asyncpraw (Client ID & Secret)
- JWT secret key for token generation
- PyMuPDF installed (pip install PyMuPDF)
- Selenium with appropriate web driver (e.g., ChromeDriver)
- LeetScrape module or equivalent scraping logic configured
- CrewAI framework installed (pip install crewai)
- DBT CLI installed and configured
- Airflow set up for pipeline scheduling
- dotenv for managing environment variables (pip install python-dotenv)
```

## Set Up the Environment
```sh
# Clone the repository
git clone https://github.com/BigDataIA-Spring25-Team-6/Final-Project.git
cd YourProjectRepo

# Ensure Python 3.10+ is installed

# Install Poetry (if not already installed)
# Follow: https://python-poetry.org/docs/#installation
# Or use the command below:
curl -sSL https://install.python-poetry.org | python3 -

# Set Poetry to not create virtualenvs outside the project (optional)
poetry config virtualenvs.in-project true

# Install project dependencies
poetry install

# Activate the virtual environment
# (Use the appropriate path based on your OS and Poetry config)
poetry shell

# Set up environment variables
# Create a .env file at the project root with the following:
# - AWS_ACCESS_KEY_ID
# - AWS_SECRET_ACCESS_KEY
# - OPENAI_API_KEY
# - PINECONE_API_KEY
# - PINECONE_ENVIRONMENT
# - SNOWFLAKE_USER, SNOWFLAKE_PASSWORD, SNOWFLAKE_ACCOUNT, etc.
# - REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET
# - JWT_SECRET

# Run FastAPI backend (inside /api folder)
cd api
poetry run uvicorn fastapi_backend:app --host 0.0.0.0 --port 8000 --reload

# Run Streamlit frontend (in a new terminal, inside /frontend folder)
cd ../frontend
poetry run streamlit run streamlit_app.py

# Optional: Run the entire system using Docker Compose from root directory
docker-compose up --build


```

## Project Structure

```
FINAL-PROJECT/

├── .github/
│   └── workflows/                   # GitHub Actions for CI/CD

├── POC/                             # Proof-of-concept experiments and prototypes

├── airflow/                         # Airflow DAGs, configs, logs, and custom scripts
│   ├── config/                      # Airflow configuration files
│   ├── dags/                        # DAG definitions
│   ├── dbt/                         # DBT models and seeds for transformations
│   ├── huggingface_cache/          # Local cache for transformers/embeddings
│   ├── logs/                        # Airflow task logs
│   ├── pinecone-sdk/               # Pinecone SDK integration or utilities
│   ├── plugins/                    # Airflow custom plugins
│   ├── scripts/                    # Custom Python scripts used by Airflow DAGs
│   └── __pycache__/                # Compiled Python cache

├── backend/                         # Backend application logic
│   ├── agents/                     # Modular AI agents (FAQAgent, MockInterviewAgent, etc.)
│   ├── api/                        # FastAPI route handlers
│   ├── data_processing/           # Reddit scraping, chunking, Pinecone integration
│   ├── utils/                      # Utility modules and helper functions
│   ├── __init__.py                 # Package initializer
│   └── pyproject.toml             # Poetry project file for backend

├── frontend/                        # Streamlit frontend for user interaction
│   ├── scripts/                    # Streamlit helper logic
│   └── pyproject.toml             # Poetry project file for frontend

├── leetscrape_service/             # Microservice or module for scraping LeetCode-like questions

├── .gitignore                       # Git ignore rules

```
