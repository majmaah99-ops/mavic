"""المنسّق — نقطة الدخول"""
import uuid
import time
from src.agents import retriever_agent, verification_agent, fiqh_agent, referral_agent
from src.security import check_input, audit_log


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

    # دمج الإجابات من عدة مصادر
    if verification["status"] in ("verified", "checkable") and sources:
        if len(sources) >= 2:
            # ادمج النصوص من المصدرين الأول والثاني
            combined = sources[0]["text"]
            # إذا كان المصدر الثاني مختلفاً ومكمّلاً، أضفه
            if sources[1]["text"][:50] not in combined:
                combined += "\n\n📌 إضافة: " + sources[1]["text"]
            answer = combined
        else:
            answer = sources[0]["text"]
        referral = None
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
