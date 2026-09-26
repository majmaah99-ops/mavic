"""الوكلاء الأربعة"""
from src.rag import search_sources
from src.security import compute_hash
from src.config import settings


class RetrieverAgent:
    name = "retriever"

    def retrieve(self, query):
        results = search_sources(query, settings.TOP_K_RESULTS)
        sources = []
        for r in results:
            if r["similarity"] < settings.SIMILARITY_THRESHOLD:
                continue
            sources.append({
                "source_id": r["source_id"],
                "text": r["text"],
                "reference": r["reference"],
                "source_type": r["source_type"],
                "authenticity": r.get("authenticity"),
                "hash": compute_hash(r["text"]),
                "similarity": r["similarity"],
            })
        return sources


class VerificationAgent:
    name = "verification"

    def verify(self, query, sources):
        if not sources:
            return {"status": "needs_review", "confidence": 0.0, "reason": "لا توجد مصادر مسترجعة"}
        verified = [s for s in sources if s.get("hash")]
        ratio = len(verified) / len(sources)
        if ratio == 1.0 and len(sources) >= 2:
            return {"status": "verified", "confidence": 0.95, "reason": f"تم التحقق من {len(verified)} مصدر"}
        if ratio >= 0.7:
            return {"status": "checkable", "confidence": 0.75, "reason": "مصادر قابلة للتحقق"}
        return {"status": "needs_review", "confidence": 0.5, "reason": "يحتاج مراجعة بشرية"}


class FiqhAgent:
    name = "fiqh"

    def is_fiqh_query(self, query):
        keywords = ["ميراث", "تركة", "زكاة", "نصاب", "فرض", "ورثة"]
        return any(k in query for k in keywords)


class ReferralAgent:
    name = "referral"

    def refer(self, reason):
        return f"لم أتمكن من تقديم إجابة موثوقة ({reason}).\n\nيرجى التواصل مع مفتي أو جهة دينية مختصة."


retriever_agent = RetrieverAgent()
verification_agent = VerificationAgent()
fiqh_agent = FiqhAgent()
referral_agent = ReferralAgent()
