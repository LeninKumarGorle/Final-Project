#with date and time
import asyncpraw
import nest_asyncio
from google.colab import userdata
from datetime import datetime
import time

# Apply nest_asyncio to handle the existing event loop in Colab
nest_asyncio.apply()

# Initialize Reddit instance using stored credentials
reddit = asyncpraw.Reddit(
    client_id=userdata.get('PRAW_CLIENT_ID'),
    client_secret=userdata.get('PRAW_CLIENT_SECRET'),
    user_agent='test'
)

async def fetch_interview_tips(subreddits, roles, companies, limit=100, min_upvotes=10):
    """
    Fetches interview tips from specified subreddits for given roles and companies.
    Filters posts by minimum upvotes and within a specified date range (2024 to 2025).
    """
    posts = []

    # Define date range: Jan 1, 2024 to Jan 1, 2025
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2025, 3, 31)
    start_timestamp = time.mktime(start_date.timetuple())
    end_timestamp = time.mktime(end_date.timetuple())

    # Compile search queries from roles and companies
    search_queries = [f"{role} interview tips {company}" for role in roles for company in companies]

    for subreddit_name in subreddits:
        subreddit = await reddit.subreddit(subreddit_name)

        for query in search_queries:
            async for post in subreddit.search(query, limit=limit, sort='relevance'):
                if (
                    post.score >= min_upvotes and
                    not post.stickied and
                    start_timestamp <= post.created_utc < end_timestamp
                ):
                    posts.append({
                        'subreddit': subreddit_name,
                        'title': post.title,
                        'selftext': post.selftext,
                        'score': post.score,
                        'url': post.url,
                        'created_utc': post.created_utc,
                        'permalink': f"https://reddit.com{post.permalink}"
                    })

    return posts

async def main():
    # List of 20 subreddits
    subreddits = [
        'cscareerquestions', 'datascience', 'dataengineering', 'MachineLearning',
        'learnprogramming', 'leetcode', 'programming', 'softwareengineering',
        'dataanalysis', 'bigdata', 'artificial', 'computerscience', 'careeradvice',
        'jobs', 'engineering', 'technology', 'developer', 'coding', 'ITCareerQuestions', 'interviews'
    ]

    # Target roles
    roles = [
        'Software Engineer', 'Data Engineer', 'Data Scientist',
        'Data Analyst', 'Machine Learning Engineer', 'AI Engineer'
    ]

    # Target companies
    companies = ['Meta', 'Amazon', 'Apple', 'Netflix', 'Google']

    # Fetch posts with custom limit per query
    results = await fetch_interview_tips(subreddits, roles, companies, limit=2)

    # Show count and sample posts
    print(f"\nTotal matching posts found: {len(results)}\n")

    for post in results:
        print(f"Subreddit: {post['subreddit']}")
        print(f"Title: {post['title']}")
        print(f"Score: {post['score']}")
        print(f"Permalink: {post['permalink']}")
        print(f"Content:\n{post['selftext'][:500]}...\n")
        print("="*80)

# Run the main async function in Colab
await main()

