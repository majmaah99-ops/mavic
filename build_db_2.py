# build_db.py - بناء قاعدة بيانات SQLite + تجهيز للفهرس الموحد
"""بناء قاعدة بيانات SQLite من ملفات hadith-json"""
import json
import sqlite3
import hashlib
from pathlib import Path

HADITH_DIR = Path("hadith-json-main/db/by_book/the_9_books")
DB_PATH = Path("data/hadith.db")

BOOKS = {
    "bukhari": "صحيح البخاري",
    "muslim": "صحيح مسلم",
}

def calc_sha256(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def build_database():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE hadiths (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book TEXT NOT NULL,
            hadith_number INTEGER,
            text TEXT NOT NULL,
            narrator TEXT,
            grade TEXT,
            sha256 TEXT
        )
    """)
    cursor.execute("CREATE INDEX idx_book ON hadiths(book)")
    cursor.execute("CREATE INDEX idx_number ON hadiths(book, hadith_number)")

    total = 0
    for book_key, book_name in BOOKS.items():
        json_file = HADITH_DIR / f"{book_key}.json"
        if not json_file.exists():
            print(f"WARNING: Not found: {json_file}")
            continue

        print(f"Processing: {book_name}...")
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        hadiths = data.get("hadiths", [])
        for h in hadiths:
            narrator = ""
            grade = ""
            grades = h.get("grades", [])
            if grades:
                narrator = grades[0].get("narrator", "")
                grade = grades[0].get("grade", "")

            text = h.get("text", "")
            sha = calc_sha256(text)

            cursor.execute("""
                INSERT INTO hadiths (book, hadith_number, text, narrator, grade, sha256)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (book_name, h.get("hadithnumber"), text, narrator, grade, sha))
            total += 1

        print(f"  OK: {len(hadiths)} hadiths")

    conn.commit()
    conn.close()
    print(f"\n✅ Total: {total} hadiths in {DB_PATH}")
    print("الآن شغل: python scripts/build_unified.py لدمجها مع PDFs")

if __name__ == "__main__":
    build_database()
