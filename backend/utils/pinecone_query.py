from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import os

# Load from .env assuming it's at the root of your backend directory
load_dotenv()

# Then access values
api_key = os.getenv("PINECONE_API_KEY")
index_name = os.getenv("INDEX_NAME")

embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def query_pinecone_chunks(query: str, role=None, company=None, api_key=None, index_name=None, top_k=5, score_threshold=0.5):
    query_embedding = embedding_model.encode(query).tolist()
    pc = Pinecone(api_key=api_key)
    index = pc.Index(index_name)

    metadata_filter = {}
    if role:
        metadata_filter["role"] = {"$eq": role}
    if company:
        metadata_filter["company"] = {"$eq": company}

    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True,
        filter=metadata_filter if metadata_filter else None,
    )

    matches = results.get("matches", [])
    filtered_matches = [m for m in matches if m["score"] >= score_threshold]

    if not filtered_matches:
        return {
            "status": "error",
            "message": "No relevant chunks found. Please ask an interview-related question.",
            "matches": []
        }

    return {
        "status": "success",
        "matches": filtered_matches
    }

    #return results