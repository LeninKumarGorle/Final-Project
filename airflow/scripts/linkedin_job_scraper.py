import sys
import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_job_description(job_url):
    try:
        res = requests.get(job_url, headers=HEADERS)
        soup = BeautifulSoup(res.text, "html.parser")
        desc = soup.find("div", class_="show-more-less-html__markup")
        return desc.get_text(separator=" ", strip=True) if desc else "N/A"
    except:
        return "N/A"

def scrape_jobs_for_role(role: str, location="United States", pages=3) -> pd.DataFrame:
    role_encoded = role.replace(" ", "%20")
    loc_encoded = location.replace(" ", "%20")
    results = []

    for start in range(0, pages * 25, 25):
        url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={role_encoded}&location={loc_encoded}&start={start}"
        resp = requests.get(url, headers=HEADERS)
        if resp.status_code != 200:
            print(f"Failed to fetch page {start} — status {resp.status_code}")
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        job_cards = soup.find_all("li")

        for job in job_cards:
            try:
                title = job.find("h3").text.strip()
                company = job.find("h4").text.strip()
                location = job.find("span", class_="job-search-card__location").text.strip()
                url = job.find("a")["href"]
                description = get_job_description(url)
                results.append({
                    "Role": role,
                    "Title": title,
                    "Company": company,
                    "Location": location,
                    "Job URL": url,
                    "Description": description
                })
                time.sleep(0.5)
            except:
                continue
        time.sleep(2)

    return pd.DataFrame(results)