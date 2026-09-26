# src/vector_store.py
import re
import hashlib
from pathlib import Path
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def normalize_ar(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'[\u064B-\u065F]', '', text)
    text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    text = text.replace('ة', 'ه').replace('ى', 'ي').replace('ـ', '')
    return text.strip()

def calc_sha256(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

class VectorStore:
    def __init__(self, cache_path="data/vector_cache.joblib"):
        self.documents = []
        self.cache_path = Path(cache_path)
        self.vectorizer = TfidfVectorizer(
            preprocessor=normalize_ar,
            token_pattern=r"(?u)\b\w+\b",
            ngram_range=(1, 2),
            lowercase=False,
            min_df=1
        )
        self.matrix = None

    def load_documents(self, docs: list):
        # نضيف SHA-256 تلقائيا لكل وثيقة
        for doc in docs:
            if "sha256" not in doc:
                doc["sha256"] = calc_sha256(doc["content"])

        self.documents = docs
        texts = [d["content"] for d in docs]
        self.matrix = self.vectorizer.fit_transform(texts)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump((self.vectorizer, self.matrix, self.documents), self.cache_path)
        print(f"[VectorStore] تم بناء الفهرس: {len(docs)} وثيقة")

    def load_cached(self) -> bool:
        if self.cache_path.exists():
            try:
                self.vectorizer, self.matrix, self.documents = joblib.load(self.cache_path)
                print(f"[VectorStore] تم تحميل الكاش: {len(self.documents)} وثيقة")
                return True
            except:
                return False
        return False

    def search(self, query: str, top_k=5):
        if self.matrix is None or not query.strip():
            return []

        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.matrix)[0]

        results = []
        for idx, score in enumerate(scores):
            if score > 0.01:
                doc = self.documents[idx]
                results.append({
                    "source_id": doc["source_id"],
                    "content": doc["content"],
                    "similarity": float(score),
                    "trust": int(float(score) * 100), # نفس نسبة الثقة اللي في الصورة 95%
                    "sha256": doc.get("sha256", calc_sha256(doc["content"])),
                    "metadata": doc.get("metadata", {}),
                    "degree": "معتمد" if float(score) > 0.5 else "يحتاج مراجعة"
                })

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]
