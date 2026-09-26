# src/vector_store.py
import re
from pathlib import Path
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def normalize_ar(text: str) -> str:
    """تطبيع بسيط ومهم للعربية"""
    if not text:
        return ""
    # إزالة التشكيل
    text = re.sub(r'[\u064B-\u065F]', '', text)
    text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    text = text.replace('ة', 'ه').replace('ى', 'ي')
    # إزالة التطويل
    text = text.replace('ـ', '')
    return text.strip()

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
            if score > 0.01: # فلتر الضوضاء
                results.append({
                    "source_id": self.documents[idx]["source_id"],
                    "content": self.documents[idx]["content"],
                    "similarity": float(score),
                    "metadata": self.documents[idx].get("metadata", {})
                })

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    def debug_search(self, query: str, top_k=5):
        results = self.search(query, top_k)
        for r in results:
            print(f"- {r['similarity']:.4f} | {r['source_id']} | {r['content'][:80]}...")
        return results
