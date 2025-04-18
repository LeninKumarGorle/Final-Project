import sys
sys.path.append("/opt/airflow")

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
from airflow.models import Variable
import pandas as pd

from scripts.coursera_scrapper import scrape_coursera_courses

default_args = {
    "start_date": days_ago(1),
    "retries": 1
}

def scrape_and_load_by_role(**context):
    job_role = context['dag_run'].conf.get("job_role")
    if not job_role:
        raise ValueError("job_role parameter not provided")

    print(f"Running scraper for job role: {job_role}")
    courses = scrape_coursera_courses(query=job_role, max_courses=300)

    # Add job role metadata
    for course in courses:
        course["job_role"] = job_role
    
    df  = pd.DataFrame(courses)
    csv_path = "/opt/airflow/dbt/course_pipeline/seeds/raw_courses.csv"
    df.to_csv(csv_path, index=False)

    print(f"Data saved to {csv_path}")

def cleanup_csv(**context):
    import os
    csv_path = "/opt/airflow/dbt/course_pipeline/seeds/raw_courses.csv"
    if os.path.exists(csv_path):
        os.remove(csv_path)
    else:
        print(f"{csv_path} does not exist, no cleanup needed.")

with DAG(
    dag_id="courses_by_job_role",
    schedule_interval=None,
    default_args=default_args,
    catchup=False,
) as dag:
    
    scrape_task = PythonOperator(
        task_id="scrape_and_load_by_role",
        python_callable=scrape_and_load_by_role,
        provide_context=True,
    )

    dbt_deps_task = BashOperator(
    task_id="dbt_deps",
    bash_command="cd /opt/airflow/dbt/course_pipeline && poetry run dbt deps --profiles-dir /opt/airflow/dbt/"
    )

    dbt_seed_task = BashOperator(
        task_id="dbt_seed",
        bash_command="cd /opt/airflow/dbt/course_pipeline && poetry run dbt seed --profiles-dir /opt/airflow/dbt/"
    )

    dbt_test_task = BashOperator(
        task_id="dbt_test",
        bash_command="cd /opt/airflow/dbt/course_pipeline && poetry run dbt test --profiles-dir /opt/airflow/dbt/"
    )

    dbt_run_task = BashOperator(
        task_id="dbt_run",
        bash_command="cd /opt/airflow/dbt/course_pipeline && poetry run dbt run --profiles-dir /opt/airflow/dbt/"
    )

    delete_csv = PythonOperator(
        task_id="delete_csv",
        python_callable=cleanup_csv,
        provide_context=True,
    )

    # Set task dependencies
    scrape_task >> dbt_deps_task >> dbt_seed_task >> dbt_run_task >> dbt_test_task >> delete_csv