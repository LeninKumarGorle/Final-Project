import sys
sys.path.append("/opt/airflow")

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
import pandas as pd
import os
from scripts.linkedin_job_scraper import scrape_jobs_for_role

def scrape_and_save(**context):
    role = context['dag_run'].conf.get("job_role", "Data Scientist") 
    df = scrape_jobs_for_role(role)

    if not df.empty:
        df.rename(columns={
            "Title": "title",
            "Company": "company",
            "Location": "location",
            "Job URL": "job_url",
            "Description": "description",
            "Role": "role"
        }, inplace=True)
        os.makedirs("/opt/airflow/dbt/job_pipeline/seeds", exist_ok=True)
        df.to_csv("/opt/airflow/dbt/job_pipeline/seeds/raw_linkedin_jobs.csv", index=False)
        print("Saved to seeds folder.")
    else:
        print("No jobs found.")


def delete_seed_csv():
    seed_file = "/opt/airflow/dbt/job_pipeline/seeds/raw_linkedin_jobs.csv"
    if os.path.exists(seed_file):
        os.remove(seed_file)
        print("Deleted seed file.")
    else:
        print("No seed file to delete.")


default_args = {
    "start_date": days_ago(1),
    "retries": 1
}

with DAG(
    dag_id="linkedin_scrape_jobs_dag",
    schedule_interval=None,
    default_args=default_args,
    catchup=False,
    params={"job_role": "Data Scientist"},
    tags=["linkedin", "etl"],
) as dag:

    scrape_task = PythonOperator(
        task_id="scrape_and_save",
        python_callable=scrape_and_save,
        provide_context=True,
    )

    seed_task = BashOperator(
        task_id="dbt_seed",
        bash_command="cd /opt/airflow/dbt/job_pipeline && poetry run dbt seed --profiles-dir /opt/airflow/dbt"
    )

    run_task = BashOperator(
        task_id="dbt_run",
        bash_command="cd /opt/airflow/dbt/job_pipeline && poetry run dbt run --profiles-dir /opt/airflow/dbt"
    )

    test_task = BashOperator(
        task_id="dbt_test",
        bash_command="cd /opt/airflow/dbt/job_pipeline && poetry run dbt test --profiles-dir /opt/airflow/dbt"
    )

    cleanup_task = PythonOperator(
        task_id="delete_seed_file",
        python_callable=delete_seed_csv,
    )

    scrape_task >> seed_task >> run_task >> test_task >> cleanup_task