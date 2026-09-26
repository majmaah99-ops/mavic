# src/retrieval.py
from src.indexer import get_store

# يتم التحميل مرة واحدة عند استيراد الموديول
store = get_store()

def search_sources(query: str, top_k: int = 5):
    """
    نفس توقيع الدالة القديمة حتى لا تكسر agents.py
    ترجع: list[dict] مع source_id, content, similarity
    """
    return store.search(query=query, top_k=top_k)

# للاختبار السريع
if __name__ == "__main__":
    q = "اذكر حديث إنما الأعمال بالنيات"
    print(f"Query: {q}")
    for r in search_sources(q, top_k=3):
        print(f"[{r['similarity']:.3f}] {r['source_id']}: {r['content']}")
