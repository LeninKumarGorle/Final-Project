# import pandas as pd
# from leetscrape import GetQuestion
# import time

# EXCEL_FILE = "D:\MS\Study\SEM - 3\DAMG 7245\Assignments\Final Assignments\Final-Project\leetscrape_POCquestions.csv"
# SHEET_NAME = 0 
# OUTPUT_COLUMN = "hasCompanyTags"

# df = pd.read_csv(EXCEL_FILE)

# if "titleSlug" not in df.columns:
#     raise ValueError("Excel must contain a 'titleSlug' column.")

# results = []
# for i, row in df.iterrows():
#     slug = row["titleSlug"]
#     print(f"[{i+1}/{len(df)}] Checking slug: {slug}")

#     try:
#         q = GetQuestion(slug).scrape()
#         has_tags = "yes" if q.Companies else "no"
#     except Exception as e:
#         print(f"❌ Error on {slug}: {e}")
#         has_tags = "error"

#     results.append(has_tags)
#     time.sleep(0.5)  # prevent hitting rate limit

# # === Step 3: Update DataFrame and Save ===
# df[OUTPUT_COLUMN] = results
# df.to_csv(EXCEL_FILE, index=False)

# print("\n✅ Done. Results saved back to:", EXCEL_FILE)

import pandas as pd
from leetscrape import GetQuestion
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

EXCEL_FILE = "D:/MS/Study/SEM - 3/DAMG 7245/Assignments/Final Assignments/Final-Project/leetscrape_POCquestions.csv"
OUTPUT_COLUMN = "hasCompanyTags"
MAX_WORKERS = 10

df = pd.read_csv(EXCEL_FILE)
slugs = df["titleSlug"].dropna().tolist()

def check_company_tag(slug):
    try:
        q = GetQuestion(slug).scrape()
        return slug, "yes" if q.Companies else "no"
    except Exception as e:
        print(f"❌ Error on {slug}: {e}")
        return slug, "error"

# Run in parallel
results_map = {}
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = {executor.submit(check_company_tag, slug): slug for slug in slugs}
    for future in as_completed(futures):
        slug, tag_status = future.result()
        results_map[slug] = tag_status

# Map results back to DataFrame
df[OUTPUT_COLUMN] = df["titleSlug"].map(results_map)

# Save back
df.to_csv(EXCEL_FILE, index=False)
print("\n✅ Done. Results saved to:", EXCEL_FILE)
