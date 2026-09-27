# src/agents/verification_agent.py
# يطابق سطر الواجهة في MAVIC.pdf: "موثّق — الثقة: %95 | تم التحقق من 2 مصدر"
from src.security.audit_log import log_query

class VerificationAgent:
    def verify(self, query: str, sources: list):
        if not sources:
            return {
                "status": "غير موثّق",
                "trust": 0,
                "trust_text": "موثّق — الثقة: 0% | تم التحقق من 0 مصدر",
                "is_verified": False,
                "answer": "لم أجد مصدر موثوق لهذا السؤال"
            }
        
        best = sources[0]
        trust = best['trust']
        count = len(sources)
        
        # منطق التوثيق كما في الصورة
        if trust >= 70:
            status = "موثّق"
        elif trust >= 40:
            status = "موثّق جزئياً"
        else:
            status = "يحتاج مراجعة"

        trust_text = f"{status} — الثقة: {trust}% | تم التحقق من {count} مصدر"

        # سجل في سلسلة التدقيق
        log_query(query, sources, trust)

        return {
            "status": status,
            "trust": trust,
            "trust_text": trust_text,
            "is_verified": trust >= 70,
            "answer": best['content'],
            "sources": sources
        }
