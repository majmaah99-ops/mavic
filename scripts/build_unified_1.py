# scripts/build_unified.py - يدمج hadith.db + PDFs في فهرس واحد 14752+
import json
import hashlib
import sqlite3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.rag.vector_store import VectorStore

def calc_sha256(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def load_from_hadith_db(db_path="data/hadith.db"):
    db_file = Path(db_path)
    if not db_file.exists():
        print(f"[UNIFIED] لا يوجد {db_path} - شغل build_db.py أولا")
        return []
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT book, hadith_number, text, narrator, grade FROM hadiths")
    rows = cursor.fetchall()
    conn.close()
    
    docs = []
    for book, num, text, narrator, grade in rows:
        if not text or len(text.strip()) < 20:
            continue
        # نظف النص
        content = text.strip()
        docs.append({
            "source_id": f"hadith_{book}_{num}",
            "content": content,
            "sha256": calc_sha256(content),
            "metadata": {
                "type": "hadith",
                "book": book,
                "hadith_number": num,
                "narrator": narrator,
                "grade": grade,
                "file": f"{book}.json"
            }
        })
    print(f"[UNIFIED] تم تحميل {len(docs)} حديث من {db_path}")
    return docs

def load_from_pdfs_json(json_path="data/sources.json"):
    jf = Path(json_path)
    if not jf.exists():
        print(f"[UNIFIED] لا يوجد {json_path} - سيتم استخدام الأحاديث فقط")
        return []
    with open(jf, 'r', encoding='utf-8') as f:
        docs = json.load(f)
    print(f"[UNIFIED] تم تحميل {len(docs)} وثيقة PDF من {json_path}")
    return docs

def main():
    # 1. حمّل من الاثنين
    hadith_docs = load_from_hadith_db()
    pdf_docs = load_from_pdfs_json()
    
    all_docs = hadith_docs + pdf_docs
    
    if not all_docs:
        print("لا يوجد أي مصدر! ضع PDFs في data/pdfs وشغل build_sources.py و build_db.py")
        return

    # 2. ابن الفهرس الموحد
    store = VectorStore(cache_path="data/vector_cache.joblib")
    store.load_documents(all_docs)
    
    # 3. احفظ JSON موحد أيضا
    unified_json = Path("data/unified_sources.json")
    with open(unified_json, 'w', encoding='utf-8') as f:
        json.dump(all_docs, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ تم بناء الفهرس الموحد: {len(all_docs)} وثيقة")
    print(f"   - أحاديث: {len(hadith_docs)}")
    print(f"   - PDF: {len(pdf_docs)}")
    print(f"   - الكاش: data/vector_cache.joblib")
    print(f"   - JSON: data/unified_sources.json")

if __name__ == "__main__":
    main()
