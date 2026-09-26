# scripts/build_sources.py
import json
from pathlib import Path
import fitz # PyMuPDF : pip install pymupdf

def pdf_to_chunks(pdf_path: Path, chunk_size=400):
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text("text") + "\n"

    # تقسيم بسيط كل 400 كلمة
    words = full_text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i+chunk_size])
        if len(chunk) > 50:
            chunks.append({
                "source_id": f"{pdf_path.stem}_{i//chunk_size:03d}",
                "content": chunk,
                "metadata": {"file": pdf_path.name, "chunk": i//chunk_size}
            })
    return chunks

def build():
    data_dir = Path("data/pdfs") # ضع كل ملفات PDF هنا
    output_path = Path("data/sources.json")

    all_docs = []
    for pdf in data_dir.glob("*.pdf"):
        print(f"معالجة {pdf.name}...")
        all_docs.extend(pdf_to_chunks(pdf))

    # أضف ملفاتك اليدوية إن وجدت
    # مثال حديث النيات يجب أن يكون وثيقة منفصلة
    all_docs.append({
        "source_id": "hadith_niyat_001",
        "content": "إنما الأعمال بالنيات وإنما لكل امرئ ما نوى فمن كانت هجرته إلى الله ورسوله فهجرته إلى الله ورسوله ومن كانت هجرته لدنيا يصيبها أو امرأة ينكحها فهجرته إلى ما هاجر إليه",
        "metadata": {"file": "hadith_niyat.pdf"}
    })

    output_path.parent.mkdir(exist_ok=True, parents=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_docs, f, ensure_ascii=False, indent=2)

    print(f"تم بناء {len(all_docs)} وثيقة في {output_path}")
    # احذف الكاش القديم
    cache = Path("data/vector_cache.joblib")
    if cache.exists():
        cache.unlink()

if __name__ == "__main__":
    build()
