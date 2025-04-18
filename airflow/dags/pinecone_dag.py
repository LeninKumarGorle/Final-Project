import sys
sys.path.append("/opt/airflow")
 
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
 
import os
from scripts.pinecone_rag import embed_texts, fetch_interview_tips, add_chunks_to_pinecone
from scripts.chunking import cluster_based_chunking
import asyncio
 
 
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}
 
dag = DAG(
    dag_id='reddit_to_pinecone_dag',
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
    description="Reddit RAG pipeline split into subtasks"
)
 
def fetch_task_fn(**kwargs):
 
    #Roles of interest
    roles = [
        'Software Engineer', 'Data Engineer', 'Data Scientist',
        'Data Analyst', 'Machine Learning Engineer', 'AI Engineer'
    ]
 
    # MAANG companies
    companies = ['Meta', 'Amazon', 'Apple', 'Netflix', 'Google']
 
    subreddits = [
        'cscareerquestions', 'datascience', 'dataengineering', 'MachineLearning',
        'learnprogramming', 'leetcode', 'programming', 'softwareengineering',
        'dataanalysis', 'bigdata', 'artificial', 'computerscience', 'careeradvice',
        'jobs', 'engineering', 'technology', 'developer', 'coding', 'ITCareerQuestions', 'interviews'
    ]
 
    praw_client_id = Variable.get("PRAW_CLIENT_ID")
    praw_client_secret = Variable.get("PRAW_CLIENT_SECRET")
    praw_user_agent = Variable.get("PRAW_USER_AGENT", default_var="airflow-reddit-bot")
 
    return asyncio.run(fetch_interview_tips(
        subreddits=subreddits,
        roles=roles,
        companies=companies,
        limit=1,
        client_id=praw_client_id,
        client_secret=praw_client_secret,
        user_agent=praw_user_agent
    ))
 
def chunk_task_fn(**kwargs):
    ti = kwargs['ti']
    posts = ti.xcom_pull(task_ids='fetch_reddit_posts')
    all_chunks = []
    for post in posts:
        text = post["title"] + "\n\n" + post["text"]
        chunks = cluster_based_chunking(text, max_chunk_size=500)
        print(f"Post: {post['title'][:50]}... → Generated {len(chunks)} chunks")
        all_chunks.append({"post": post, "chunks": chunks})
    return all_chunks
 
def embed_task_fn(**kwargs):
    ti = kwargs['ti']
    chunked_data = ti.xcom_pull(task_ids='chunk_reddit_posts')
    embedded_data = []
    for entry in chunked_data:
        post = entry["post"]
        chunks = entry["chunks"]
        embeddings = embed_texts(chunks).tolist()
        embedded_data.append({"post": post, "chunks": chunks, "embeddings": embeddings})
    return embedded_data
 
def upload_task_fn(**kwargs):
    ti = kwargs['ti']
    embedded_data = ti.xcom_pull(task_ids='embed_chunks')
 
    pinecone_api_key = Variable.get("PINECONE_API_KEY")
    pinecone_env = Variable.get("PINECONE_ENV")
    index_name = Variable.get("INDEX_NAME", default_var="fp-reddit-test")
 
    if not pinecone_api_key or not pinecone_env or not index_name:
        raise ValueError("Missing Pinecone configuration (API key, environment, or index name)")
    print(f"Pinecone config — index: {index_name}, env: {pinecone_env}, key present: {bool(pinecone_api_key)}")
    print(f"Total entries to upload: {len(embedded_data)}")
 
    for entry in embedded_data:
        post = entry["post"]
        chunks = entry["chunks"]
        role = post.get("role", "Unknown")
        company = post.get("company", "Unknown")
        count = add_chunks_to_pinecone(
            chunks, post, role=role, company=company,
            api_key=pinecone_api_key, environment=pinecone_env, index_name=index_name
        )
        print(f"Uploaded {count} vectors to Pinecone for post ID: {post.get('id')}")
    print("Upload complete.")
 
fetch_task = PythonOperator(
    task_id='fetch_reddit_posts',
    python_callable=fetch_task_fn,
    dag=dag,
)
 
chunk_task = PythonOperator(
    task_id='chunk_reddit_posts',
    python_callable=chunk_task_fn,
    dag=dag,
)
 
embed_task = PythonOperator(
    task_id='embed_chunks',
    python_callable=embed_task_fn,
    dag=dag,
)
 
upload_task = PythonOperator(
    task_id='upload_to_pinecone',
    python_callable=upload_task_fn,
    dag=dag,
)
 
fetch_task >> chunk_task >> embed_task >> upload_task