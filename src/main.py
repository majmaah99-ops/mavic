"""المنسّق — نقطة الدخول"""
import re
import uuid
import time
from src.agents import retriever_agent, verification_agent, fiqh_agent, referral_agent
from src.security import check_input, audit_log


STOP_WORDS = {
    "ما", "من", "في", "على", "إلى", "عن", "هذا", "هذه", "ذلك", "تلك",
    "التي", "الذي", "الذين", "إن", "أن", "كان", "كانت", "يكون",
    "هو", "هي", "هم", "هن", "أنا", "أنت", "نحن", "أنتم",
    "هل", "كيف", "لماذا", "متى", "أين", "كم", "أي",
    "و", "أو", "ثم", "لكن", "بل", "لا", "لم", "لن", "قد", "كل",
    "بعض", "غير", "بين", "مع", "عند", "قبل", "بعد",
    "اذكر", "أعطني", "قل", "أخبرني", "حدثني", "وضح", "اشرح",
}


def _get_keywords(text):
    """استخراج الكلمات المفتاحية من النص"""
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
    text = re.sub(r"[^\w\s\u0600-\u06FF]", " ", text)
    text = re.sub(r"[إأآا]", "ا", text)
    text = re.sub(r"[ىي]", "ي", text)
    text = re.sub(r"ة", "ه", text)
    words = text.lower().split()
    return set(w for w in words if len(w) > 2 and w not in STOP_WORDS)


def _is_relevant(query, source_text, min_overlap=2):
    """التحقق من أن المصدر ذو صلة بالسؤال"""
    query_kws = _get_keywords(query)
    source_kws = _get_keywords(source_text)

    if not query_kws or not source_kws:
        return False

    overlap = query_kws & source_kws
    return len(overlap) >= min_overlap


def ask(query):
    ok, reason = check_input(query)
    if not ok:
        return {"error": reason}

    start = time.perf_counter()
    query_id = f"q_{uuid.uuid4().hex[:12]}"
    agents_used = []

    if fiqh_agent.is_fiqh_query(query):
        agents_used.append("fiqh")

    agents_used.append("retriever")
    sources = retriever_agent.retrieve(query)
    sources_data = [{"source_id": s["source_id"]} for s in sources]

    agents_used.append("verification")
    verification = verification_agent.verify(query, sources)

    # فلترة المصادر: احتفظ فقط بالمصادر ذات الصلة بالسؤال
    if verification["status"] in ("verified", "checkable") and sources:
        relevant_sources = []
        for s in sources:
            if _is_relevant(query, s["text"], min_overlap=2):
                relevant_sources.append(s)

        # إذا لم ينجح الفلتر الصارم، استخدم المصدر الأول فقط
        if not relevant_sources:
            relevant_sources = [sources[0]]

        # الإجابة = المصدر الأول الموثوق فقط
        # (لا ندمج مصادر متعددة لأنها قد تخلط المواضيع)
        answer = relevant_sources[0]["text"]

        # إذا كان هناك مصدر ثانٍ شديد الصلة، أضفه
        if len(relevant_sources) >= 2:
            second_kws = _get_keywords(relevant_sources[1]["text"])
            query_kws = _get_keywords(query)
            second_overlap = query_kws & second_kws

            # اشتراط تطابق قوي (3 كلمات على الأقل)
            if len(second_overlap) >= 3:
                answer += "\n\n📌 إضافة: " + relevant_sources[1]["text"]

        referral = None
        # استخدام المصادر المُفلترة في العرض
        sources = relevant_sources
    else:
        agents_used.append("referral")
        answer = None
        referral = referral_agent.refer(verification["reason"])

    elapsed_ms = (time.perf_counter() - start) * 1000
    elapsed_ms = round(elapsed_ms, 2)
    if elapsed_ms < 0.1:
        elapsed_ms = 0.1

    audit_log.log(query_id, query, agents_used, sources_data, verification["status"])

    return {
        "query": query,
        "answer": answer,
        "sources": sources,
        "verification": verification,
        "referral": referral,
        "processing_time_ms": elapsed_ms,
        "query_id": query_id,
    }
