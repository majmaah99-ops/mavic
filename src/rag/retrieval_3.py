# src/rag/retrieval.py
from .indexer import get_store

def search_sources(query: str, top_k=5):
    store = get_store()
    if not store.documents:
        return []
    return store.search(query, top_k=top_k)
