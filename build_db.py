# build_db.py
"""بناء قاعدة بيانات SQLite من ملفات hadith-json"""
import json
import sqlite3
from pathlib import Path

HADITH_DIR = Path("hadith-json-main/db/by_book/the_9_books")
DB_PATH = Path("data/hadith.db")

# الكتب التي نريد دمجها
BOOKS = {
    "bukhari": "صحيح البخاري",
    "muslim": "صحيح مسلم",
}


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
            grade TEXT
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

            cursor.execute("""
                INSERT INTO hadiths (book, hadith_number, text, narrator, grade)
                VALUES (?, ?, ?, ?, ?)
            """, (
                book_name,
                h.get("hadithnumber"),
                h.get("text", ""),
                narrator,
                grade,
            ))
            total += 1

        print(f"  OK: {len(hadiths)} hadiths")

    conn.commit()
    conn.close()

    size_mb = DB_PATH.stat().st_size / (1024 * 1024)
    print(f"\nSUCCESS: Database built!")
    print(f"Path: {DB_PATH}")
    print(f"Total: {total} hadiths")
    print(f"Size: {size_mb:.2f} MB")


if __name__ == "__main__":
    build_database()
