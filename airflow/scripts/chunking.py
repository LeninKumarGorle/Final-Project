### Modified chunking.py: Keeping only Cluster-Based Chunking
import re
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Load Sentence Transformer model (cached)
embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", cache_folder="/opt/airflow/huggingface_cache")

# Function to tokenize sentences
def tokenize_sentences(text):
    return re.split(r'(?<=[.!?])\s+', text)

# Function to compute embeddings
def compute_embeddings(sentences):
    return embedding_model.encode(sentences, convert_to_numpy=True, batch_size=8)

def cluster_based_chunking(document, max_chunk_size=500, similarity_threshold=0.75):
    sentences = tokenize_sentences(document)
    embeddings = compute_embeddings(sentences)

    clusters = []
    current_chunk = []
    current_size = 0

    for i, sentence in enumerate(sentences):
        sentence_length = len(sentence)

        if i == 0:
            current_chunk.append(sentence)
            current_size += sentence_length
            continue

        similarity = cosine_similarity([embeddings[i]], [embeddings[i-1]])[0][0]

        if similarity > similarity_threshold and (current_size + sentence_length) <= max_chunk_size:
            current_chunk.append(sentence)
            current_size += sentence_length
        else:
            clusters.append(" ".join(current_chunk))
            current_chunk = [sentence]
            current_size = sentence_length

    if current_chunk:
        clusters.append(" ".join(current_chunk))

    return clusters