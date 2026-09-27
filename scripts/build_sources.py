import json
import hashlib
from pathlib import Path
import fitz

def calc_sha256(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def pdf_to_chunks(pdf_path: Path, chunk_size=400):
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text("text") + "\n"
    words = full_text.split()
    if not words:
        return []
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk_text = " ".join(words[i:i+chunk_size])
        if len(chunk_text.strip()) < 50:
            continue
        chunks.append({
            "source_id": f"{pdf_path.stem}_{i//chunk_size:03d}",
            "content": chunk_text,
            "sha256": calc_sha256(chunk_text),
            "metadata": {"file": pdf_path.name, "chunk_index": i//chunk_size}
        })
    return chunks

def main():
    pdfs_dir = Path("data/pdfs")
    output_file = Path("data/sources.json")
    cache_file = Path("data/vector_cache.joblib")
    pdfs_dir.mkdir(parents=True, exist_ok=True)
    all_chunks = []
    for pdf_path in pdfs_dir.glob("*.pdf"):
        print(f"معالجة {pdf_path.name}...")
        all_chunks.extend(pdf_to_chunks(pdf_path))
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)
    print(f"تم بناء {len(all_chunks)} وثيقة")
    if cache_file.exists():
        cache_file.unlink()

if __name__ == "__main__":
    main()
