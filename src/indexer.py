# src/rag/indexer.py
from pathlib import Path
import json
from .vector_store import VectorStore

def get_store(sources_path="data/sources.json", cache_path="data/vector_cache.joblib"):
    store = VectorStore(cache_path=cache_path)
    if store.load_cached():
        return store
    sources_file = Path(sources_path)
    if not sources_file.exists():
        return store
    with open(sources_file, 'r', encoding='utf-8') as f:
        docs = json.load(f)
    store.load_documents(docs)
    return store
