# src/agents/fiqh_agent.py
class FiqhAgent:
    def classify(self, query: str) -> str:
        q = query.lower()
        if "صلاة" in query or "صوم" in query or "زكاة" in query or "حج" in query:
            return "عبادات"
        if "نكاح" in query or "طلاق" in query or "بيع" in query:
            return "معاملات"
        return "عام"
