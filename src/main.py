"""المنسّق — نقطة الدخول"""
import uuid
import time
from src.agents import retriever_agent, verification_agent, fiqh_agent, referral_agent
from src.security import check_input, audit_log


def ask(query):
    ok, reason = check_input(query)
    if not ok:
        return {"error": reason}

    start = time.time()
    query_id = f"q_{uuid.uuid4().hex[:12]}"
    agents_used = []

    if fiqh_agent.is_fiqh_query(query):
        agents_used.append("fiqh")

    agents_used.append("retriever")
    sources = retriever_agent.retrieve(query)
    sources_data = [{"source_id": s["source_id"]} for s in sources]

    agents_used.append("verification")
    verification = verification_agent.verify(query, sources)

    if verification["status"] in ("verified", "checkable") and sources:
        answer = sources[0]["text"]
        referral = None
    else:
        agents_used.append("referral")
        answer = None
        referral = referral_agent.refer(verification["reason"])

    elapsed = (time.time() - start) * 1000

    audit_log.log(query_id, query, agents_used, sources_data, verification["status"])

    return {
        "query": query,
        "answer": answer,
        "sources": sources,
        "verification": verification,
        "referral": referral,
        "processing_time_ms": elapsed,
        "query_id": query_id,
    }
