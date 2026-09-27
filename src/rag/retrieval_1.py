# src/rag/retrieval.py - بحث موحد
from .indexer import get_store

def search_sources(query: str, top_k=5, filter_type=None):
    """
    filter_type: None = الكل, "hadith" = أحاديث فقط, "fiqh" = فقه فقط
    """
    store = get_store()
    if not store.documents:
        return []
    
    results = store.search(query, top_k=top_k*2)  # نجيب أكثر ثم نفلتر
    
    if filter_type:
        results = [r for r in results if r['metadata'].get('type') == filter_type]
    
    return results[:top_k]

# اختبار
if __name__ == "__main__":
    tests = ["ما حكم صلاة المسافر", "إنما الأعمال بالنيات", "حكم الوتر"]
    for q in tests:
        print(f"\n🔍 {q}")
        res = search_sources(q, top_k=2)
        for r in res:
            print(f"  [{r['trust']}%] {r['source_id']} - {r['content'][:60]}...")
