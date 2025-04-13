import requests
from requests.auth import HTTPBasicAuth

def unpause_and_trigger_dag(job_role):
    AIRFLOW_BASE_URL = "http://localhost:8080"
    DAG_ID = "courses_by_job_role"
    AUTH = HTTPBasicAuth("airflow", "airflow") 

    # Step 1: Unpause the DAG
    unpause_url = f"{AIRFLOW_BASE_URL}/api/v1/dags/{DAG_ID}"
    print(unpause_url)
    unpause_payload = {"is_paused": False}

    unpause_response = requests.patch(unpause_url, json=unpause_payload, auth=AUTH)
    print(unpause_response.status_code)
    if unpause_response.status_code == 200:
        print("DAG unpaused successfully.")
    else:
        print(f"Failed to unpause DAG. Status: {unpause_response.status_code}, Response: {unpause_response.text}")
        return

    # Step 2: Trigger the DAG
    trigger_url = f"{AIRFLOW_BASE_URL}/api/v1/dags/{DAG_ID}/dagRuns"
    trigger_payload = {"conf": {"job_role": job_role}}

    trigger_response = requests.post(trigger_url, json=trigger_payload, auth=AUTH)
    if trigger_response.status_code == 200:
        print("DAG triggered successfully.")
    else:
        print(f"Failed to trigger DAG. Status: {trigger_response.status_code}, Response: {trigger_response.text}")
    
    print("Trigger Response:", trigger_response.json())

# Example usage
unpause_and_trigger_dag("data analyst")
