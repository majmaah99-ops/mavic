# src/indexer.py
import json
from pathlib import Path
from src.vector_store import VectorStore

_store_instance = None

def get_store(force_rebuild=False):
    global _store_instance
    if _store_instance is not None and not force_rebuild:
        return _store_instance

    store = VectorStore()

    if not force_rebuild and store.load_cached():
        _store_instance = store
        return store

    # بناء من الصفر
    data_path = Path("data/sources.json")
    if not data_path.exists():
        raise FileNotFoundError(f"لم أجد {data_path}. شغل أولاً scripts/build_sources.py")

    with open(data_path, "r", encoding="utf-8") as f:
        docs = json.load(f)

    store.load_documents(docs)
    _store_instance = store
    return store

def build_index():
    return get_store(force_rebuild=True)
