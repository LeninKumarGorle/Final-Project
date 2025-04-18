import logging
import asyncpraw
import time
from datetime import datetime
from pinecone import Pinecone, ServerlessSpec
from scripts.chunking import embedding_model
import uuid
from scripts.validations import is_valid_post

# Embed text using the sentence transformer model
def embed_texts(texts):
    return embedding_model.encode(texts, convert_to_numpy=True)

# Ensure Pinecone index exists
def get_or_create_index(api_key, environment, index_name):
    pc = Pinecone(api_key=api_key)
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=384,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region=environment)
        )
    return pc.Index(index_name)

def add_chunks_to_pinecone(chunks, post, role=None, company=None, api_key=None, environment=None, index_name=None):

    if not chunks:
        print("No chunks to upload.")
        return 0
    
    index = get_or_create_index(api_key, environment, index_name)

    embeddings = embed_texts(chunks)
    ids = [f"{post['id']}_chunk_{i}_{uuid.uuid4().hex[:6]}" for i in range(len(chunks))]

    metadatas = [{
        "source": post["id"],
        "chunk_index": i,
        "text": chunks[i],
        "title": post["title"],
        "subreddit": post["subreddit"],
        "permalink": f"https://reddit.com/r/{post['subreddit']}/comments/{post['id']}",
        "role": role,
        "company": company
    } for i in range(len(chunks))]
    print(f"Upserting {len(chunks)} vectors to index: {index_name}")
    index.upsert(vectors=[(ids[i], embeddings[i].tolist(), metadatas[i]) for i in range(len(chunks))])
    return len(chunks)

# Reddit async scraper
def init_reddit(client_id, client_secret, user_agent):
    if not all([client_id, client_secret, user_agent]):
        raise ValueError("❌ Missing Reddit credentials. Check environment variables.")
    return asyncpraw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent
    )

logger = logging.getLogger(__name__)

async def fetch_interview_tips(subreddits, roles, companies, limit=1, min_upvotes=10,
                                client_id=None, client_secret=None, user_agent=None):
    reddit = init_reddit(client_id, client_secret, user_agent)
    posts = []

    start_date = datetime(2024, 1, 1)
    end_date = datetime(2025, 3, 31)
    start_timestamp = time.mktime(start_date.timetuple())
    end_timestamp = time.mktime(end_date.timetuple())

    try:
        for role in roles:
            for company in companies:
                query = f"{role} interview tips {company}"
                logger.info(f"🔍 Processing query: '{query}'")

                for subreddit_name in subreddits:
                    logger.info(f"📚 Searching in subreddit: r/{subreddit_name}")
                    try:
                        subreddit = await reddit.subreddit(subreddit_name)
                        async for post in subreddit.search(query, limit=limit, sort='relevance'):
                            if (
                                post.score >= min_upvotes and
                                not post.stickied and
                                start_timestamp <= post.created_utc < end_timestamp
                            ):
                                post_dict = {
                                    'id': post.id,
                                    'title': post.title,
                                    'selftext': post.selftext,
                                    'subreddit': subreddit_name,
                                    'role': role,
                                    'company': company
                                }

                                if is_valid_post(post_dict):  # ✅ Apply validation
                                    logger.info(f"✅ Valid post: {post.title} (score: {post.score})")
                                    # Rename selftext -> text to match downstream pipeline
                                    post_dict['text'] = post_dict.pop('selftext')
                                    posts.append(post_dict)
                                else:
                                    logger.info(f"⛔ Skipped invalid post: {post.id}")
                    except Exception as search_err:
                        logger.error(f"❌ Error searching subreddit '{subreddit_name}' for query '{query}': {search_err}", exc_info=True)
    except Exception as e:
        logger.error(f"🔥 Unexpected error in fetch_interview_tips: {e}", exc_info=True)
        raise
    finally:
        await reddit.close()
        logger.info("🔒 Reddit client connection closed.")

    logger.info(f"📦 Total posts collected after validation: {len(posts)}")
    posts = posts[:5]  # optionally cap the number
    return posts