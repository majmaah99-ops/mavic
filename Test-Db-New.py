# test_db.py - اختبار الفهرس الموحد MAVIC
import sqlite3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

# حاول استيراد الفهرس الموحد
try:
    from src.rag.retrieval import search_sources
    from src.rag.indexer import get_store
    HAS_VECTOR = True
except Exception as e:
    print(f"⚠️ لا يمكن تحميل الفهرس الموحد: {e}")
    HAS_VECTOR = False

print("="*60)
print("🧪 اختبار MAVIC الموحد")
print("="*60)

# اختبار 1: SQLite
print("\n[1] اختبار hadith.db (SQLite)")
db_path = Path("data/hadith.db")
if db_path.exists():
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM hadiths")
    total = cur.fetchone()[0]
    print(f"  Total hadiths: {total}")
    cur.execute("SELECT book, COUNT(*) FROM hadiths GROUP BY book")
    for book, count in cur.fetchall():
        print(f"    {book}: {count}")
    conn.close()
else:
    print("  ❌ لا يوجد data/hadith.db - شغل python build_db.py")

# اختبار 2: الكاش الموحد
print("\n[2] اختبار vector_cache.joblib (الفهرس الموحد)")
cache_path = Path("data/vector_cache.joblib")
if cache_path.exists():
    size_mb = cache_path.stat().st_size / (1024*1024)
    print(f"  ✅ يوجد الكاش: {size_mb:.2f} MB")
    if HAS_VECTOR:
        store = get_store()
        print(f"  📚 عدد الوثائق في الفهرس: {len(store.documents)}")
        # عد الأنواع
        from collections import Counter
        types = Counter([d.get('metadata', {}).get('type', 'pdf') for d in store.documents])
        for t, c in types.items():
            print(f"    - {t}: {c}")
else:
    print("  ❌ لا يوجد vector_cache - شغل python scripts/build_unified.py")

# اختبار 3: البحث الموحد (هذا اللي يطابق واجهة الصورة)
print("\n[3] اختبار البحث الموحد (مثل واجهة MAVIC.pdf)")

if not HAS_VECTOR:
    print("  تخطي - الفهرس غير محمل")
else:
    tests = [
        "النيات",
        "الوتر", 
        "ما حكم صلاة المسافر"
    ]
    
    for q in tests:
        print(f"\n  🔍 البحث عن: '{q}'")
        results = search_sources(q, top_k=2)
        print(f"  Found: {len(results)} نتائج")
        
        if not results:
            print("    لا يوجد نتائج")
            continue
            
        for r in results:
            print(f"\n    [{r['trust']}%] {r['source_id']}")
            print(f"    degree: {r['degree']}")
            print(f"    SHA-256: {r['sha256'][:32]}...")
            print(f"    content: {r['content'][:80]}...")
            
            # هذا هو السطر اللي يظهر في الواجهة
            print(f"    >> موثّق — الثقة: {r['trust']}% | مصدر: {r['source_id']}")

# اختبار 4: سجل التدقيق
print("\n[4] اختبار سجل التدقيق")
audit_path = Path("data/audit_log.jsonl")
if audit_path.exists():
    with open(audit_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    print(f"  📝 سجل التدقيق: {len(lines)} عملية (مثل الصورة: 6)")
    if lines:
        print(f"  آخر عملية: {lines[-1][:100]}...")
else:
    print("  لا يوجد سجل بعد - سيظهر بعد أول بحث في streamlit")

print("\n" + "="*60)
print("✅ اكتمل الاختبار الموحد!")
print("شغل: streamlit run app/streamlit_app.py لترى الواجهة")
print("="*60)
