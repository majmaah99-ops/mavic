"""طبقة الأمن: منع الحقن + سجل التدقيق + سلامة المصادر"""
import re
import json
import hashlib
from datetime import datetime
from pathlib import Path
from src.config import settings


SUSPICIOUS_PATTERNS = [
    r"ignore\s+(previous|all)\s+instructions",
    r"تجاهل\s+(التعليمات|كل)\s+السابقة",
    r"you\s+are\s+now\s+",
    r"system\s*:\s*",
    r"<\s*script",
    r"DROP\s+TABLE",
    r"eval\s*\(",
]


def check_input(text):
    if not text or not text.strip():
        return False, "المدخل فارغ"
    if len(text) > settings.MAX_QUERY_LENGTH:
        return False, f"المدخل يتجاوز {settings.MAX_QUERY_LENGTH} حرف"
    for p in SUSPICIOUS_PATTERNS:
        if re.search(p, text, re.IGNORECASE):
            return False, "تم رفض الطلب لأسباب أمنية"
    return True, "OK"


def compute_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class AuditLog:
    def __init__(self, path=None):
        self.path = Path(path or settings.AUDIT_LOG_PATH)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._last = self._read_last()

    def _read_last(self):
        if not self.path.exists():
            return "GENESIS"
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if not lines:
                    return "GENESIS"
                return json.loads(lines[-1]).get("current_hash", "GENESIS")
        except Exception:
            return "GENESIS"

    def _compute(self, data, prev):
        payload = json.dumps(data, sort_keys=True, ensure_ascii=False) + prev + settings.SOURCE_HASH_SALT
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def log(self, query_id, query, agents, sources, result):
        data = {
            "query_id": query_id,
            "user_query_hash": hashlib.sha256(query.encode()).hexdigest()[:16],
            "timestamp": datetime.utcnow().isoformat(),
            "agents_involved": agents,
            "sources_retrieved": sources,
            "verification_result": result,
        }
        h = self._compute(data, self._last)
        entry = {**data, "previous_hash": self._last, "current_hash": h}
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self._last = h
        return entry

    def verify_chain(self):
        if not self.path.exists():
            return True
        prev = "GENESIS"
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                entry = json.loads(line)
                data = {k: v for k, v in entry.items() if k not in ("previous_hash", "current_hash")}
                if self._compute(data, prev) != entry["current_hash"]:
                    return False
                prev = entry["current_hash"]
        return True

    def count(self):
        if not self.path.exists():
            return 0
        with open(self.path, "r", encoding="utf-8") as f:
            return sum(1 for _ in f)


audit_log = AuditLog()
