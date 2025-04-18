from fastapi import FastAPI
from leetscrape import GetQuestionsList, GetQuestion
import pandas as pd
import html2text

h2t = html2text.HTML2Text()
h2t.ignore_links = False

app = FastAPI()
question_cache = {}

@app.get("/questions/{topic}")
def get_questions(topic: str):
    if topic not in question_cache:
        scraper = GetQuestionsList()
        scraper.scrape()
        df = scraper.questions
        filtered = df[df['topicTags'].str.contains(topic, case=False)]
        question_cache[topic] = filtered[['titleSlug', 'title', 'difficulty']].to_dict(orient='records')
    return {"questions": question_cache[topic][:5]}

@app.get("/question-detail/{slug}")
def get_question_detail(slug: str):
    q = GetQuestion(titleSlug=slug).scrape()
    clean_description = h2t.handle(q.Body)

    return {
        "title": q.title,
        "difficulty": q.difficulty,
        "topics": q.topics,
        "description": clean_description,
        "code_stub": q.Code
    }
