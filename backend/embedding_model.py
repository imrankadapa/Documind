from sentence_transformers import SentenceTransformer

def load_embedding_model():
    return SentenceTransformer("all-MiniLM-L6-v2")