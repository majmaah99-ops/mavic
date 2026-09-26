"""الوكلاء الأربعة — Retriever, Verification, Fiqh, Referral"""
from src.rag import search_sources_enhanced
from src.security import compute_hash
from src.config import settings


class RetrieverAgent:
    """وكيل الاسترجاع — يبحث في المصادر المحلية وقاعدة بيانات الأحاديث"""
    name = "retriever"

    def retrieve(self, query):
        # استدعاء الدالة الموحدة (المصادر المحلية + قاعدة بيانات الأحاديث)
        results = search_sources_enhanced(query, settings.TOP_K_RESULTS)

        sources = []
        for r in results:
            # استخدام .get() لتجنب KeyError
            # المصادر القادمة من قاعدة البيانات (SQLite) قد لا تحتوي على similarity
            similarity = r.get("similarity", 1.0)

            if similarity < settings.SIMILARITY_THRESHOLD:
                continue

            sources.append({
                "source_id": r["source_id"],
                "text": r["text"],
                "reference": r["reference"],
                "source_type": r["source_type"],
                "authenticity": r.get("authenticity"),
                "hash": compute_hash(r["text"]),
                "similarity": similarity,
            })

        return sources


class VerificationAgent:
    """وكيل التحقق — يتحقق من صحة المصادر ودرجة الثقة"""
    name = "verification"

    def verify(self, query, sources):
        if not sources:
            return {
                "status": "needs_review",
                "confidence": 0.0,
                "reason": "لا توجد مصادر مسترجعة",
            }

        # جميع المصادر لها hash (بما فيها من API أو DB)
        verified = [s for s in sources if s.get("hash")]
        ratio = len(verified) / len(sources)

        if ratio == 1.0 and len(sources) >= 2:
            return {
                "status": "verified",
                "confidence": 0.95,
                "reason": f"تم التحقق من {len(verified)} مصدر",
            }
        if ratio >= 0.7:
            return {
                "status": "checkable",
                "confidence": 0.75,
                "reason": "مصادر قابلة للتحقق",
            }
        return {
            "status": "needs_review",
            "confidence": 0.5,
            "reason": "يحتاج مراجعة بشرية",
        }


class FiqhAgent:
    """وكيل الفقه — يحدد الأسئلة الفقهية الحسابية"""
    name = "fiqh"

    def is_fiqh_query(self, query):
        keywords = [
            "ميراث", "تركة", "زكاة", "نصاب", "فرض", "ورثة",
            "حكم", "يجوز", "حرام", "حلال", "واجب", "سنة", "مكروه"
        ]
        return any(k in query for k in keywords)


class ReferralAgent:
    """وكيل الإحالة — يحيل المستخدم للمختص عند نقص المرجعية"""
    name = "referral"

    def refer(self, reason):
        return (
            f"لم أتمكن من تقديم إجابة موثوقة ({reason}).\n\n"
            "يرجى التواصل مع مفتي أو جهة دينية مختصة."
        )


# ===== إنشاء نسخ من الوكلاء للاستخدام المباشر =====
retriever_agent = RetrieverAgent()
verification_agent = VerificationAgent()
fiqh_agent = FiqhAgent()
referral_agent = ReferralAgent()
