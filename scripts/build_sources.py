# scripts/build_sources.py
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
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i+chunk_size])
        if len(chunk) > 50:
            chunks.append({
                "source_id": f"{pdf_path.stem}_{i//chunk_size:03d}",
                "content": chunk,
                "sha256": calc_sha256(chunk),
                "metadata": {"file": pdf_path.name, "chunk": i//chunk_size}
            })
    return chunks
