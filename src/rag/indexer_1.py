# src/rag/indexer.py - يدعم hadith.db + PDFs تلقائيا
from pathlib import Path
import json
import sqlite3
import hashlib
from .vector_store import VectorStore

def calc_sha256(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def load_from_db_and_json():
    docs = []
    # 1. من hadith.db
    db_path = Path("data/hadith.db")
    if db_path.exists():
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        try:
            cur.execute("SELECT book, hadith_number, text, narrator, grade FROM hadiths")
            for book, num, text, narrator, grade in cur.fetchall():
                if text and len(text.strip()) > 20:
                    docs.append({
                        "source_id": f"hadith_{book}_{num}",
                        "content": text.strip(),
                        "sha256": calc_sha256(text.strip()),
                        "metadata": {"type": "hadith", "book": book, "hadith_number": num, "grade": grade}
                    })
        except:
            pass
        conn.close()
    
    # 2. من unified أو sources
    for json_file in ["data/unified_sources.json", "data/sources.json"]:
        jf = Path(json_file)
        if jf.exists():
            try:
                with open(jf, 'r', encoding='utf-8') as f:
                    jdocs = json.load(f)
                    # تجنب التكرار إذا كان unified موجود
                    if json_file == "data/unified_sources.json":
                        return jdocs
                    docs.extend(jdocs)
            except:
                pass
    return docs

def get_store(sources_path="data/unified_sources.json", cache_path="data/vector_cache.joblib"):
    store = VectorStore(cache_path=cache_path)
    if store.load_cached() and store.documents:
        print(f"[Indexer] تم تحميل الكاش الموحد: {len(store.documents)} وثيقة")
        return store
    
    docs = load_from_db_and_json()
    if not docs:
        print("[Indexer] لا يوجد مصادر - شغل build_unified.py")
        return store
    
    store.load_documents(docs)
    return store
