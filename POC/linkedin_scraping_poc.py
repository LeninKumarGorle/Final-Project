import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# Target roles and location
job_roles = [
    "Software Engineer",
    "Data Engineer",
    "Data Scientist",
    "Data Analyst",
    "Machine Learning Engineer",
    "AI Engineer"
]
location = "United States"

headers = {
    "User-Agent": "Mozilla/5.0"
}

# Function to get full job description from job URL
def get_job_description(job_url):
    try:
        response = requests.get(job_url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            desc = soup.find("div", class_="show-more-less-html__markup")
            return desc.get_text(separator=" ", strip=True) if desc else "N/A"
        else:
            print(f"Failed to fetch job page: {job_url} (Status: {response.status_code})")
            return "N/A"
    except Exception as e:
        print(f"Error fetching job description for {job_url}: {e}")
        return "N/A"

# Function to collect job metadata and description
def get_linkedin_jobs(role, location="United States", pages=5):
    role_encoded = role.replace(" ", "%20")
    location_encoded = location.replace(" ", "%20")
    all_jobs = []

    for start in range(0, pages * 25, 25):
        url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={role_encoded}&location={location_encoded}&start={start}"
        print(f"Fetching: {role} (page {start // 25 + 1})")
        try:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                print(f"Failed to fetch listings (Status: {response.status_code})")
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            job_cards = soup.find_all("li")

            for job in job_cards:
                try:
                    title = job.find("h3").text.strip()
                    company = job.find("h4").text.strip()
                    job_location = job.find("span", class_="job-search-card__location").text.strip()
                    job_url = job.find("a")["href"]

                    # NEW: Fetch job description
                    description = get_job_description(job_url)
                    time.sleep(1)  # polite delay

                    all_jobs.append({
                        "Role": role,
                        "Title": title,
                        "Company": company,
                        "Location": job_location,
                        "Job URL": job_url,
                        "Description": description
                    })
                except Exception as e:
                    print("Error reading job card:", e)

        except Exception as e:
            print(f"Error fetching jobs for role {role}: {e}")

        time.sleep(2)  # avoid getting blocked
    return all_jobs

# Master list
all_results = []

# Loop through each role
for role in job_roles:
    jobs = get_linkedin_jobs(role)
    print(f"Found {len(jobs)} jobs for {role}")
    all_results.extend(jobs)

# Save to CSV and Excel
df = pd.DataFrame(all_results)
df.to_csv("linkedin_jobs_with_descriptions.csv", index=False)
df.to_excel("linkedin_jobs_with_descriptions.xlsx", index=False)

print(f"\nDone! Scraped {len(df)} total jobs with descriptions.")
