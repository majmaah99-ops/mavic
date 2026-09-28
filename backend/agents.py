"""MAVIC agents - نص بحث بدون ChromaDB"""
import hashlib, json, re, uuid
from datetime import datetime
from pathlib import Path
from difflib import SequenceMatcher

ROOT = Path(__file__).parent.parent
AUDIT_FILE = ROOT / "data" / "audit.jsonl"
SOURCES_DIR = ROOT / "sources"

_CACHE = None

def _load_sources():
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    items = []
    if not SOURCES_DIR.exists():
        _CACHE = items
        return items
    for cat_dir in SOURCES_DIR.iterdir():
        if not cat_dir.is_dir():
            continue
        for f in cat_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                for it in data:
                    items.append({
                        "text": str(it.get("text", "")),
                        "source_id": str(it.get("id", "")),
                        "book": str(it.get("book", "")),
                        "number": str(it.get("number", "")),
                        "category": cat_dir.name,
                        "sha": hashlib.sha256(str(it.get("text", "")).encode()).hexdigest()[:16],
                    })
            except Exception:
                pass
    _CACHE = items
    print(f"📚 Loaded {len(items)} sources into memory")
    return items

def _normalize(s):
    s = re.sub(r"[\u064B-\u0652\u0670\u0640]", "", s)
    s = re.sub(r"[إأآا]", "ا", s)
    s = re.sub(r"[ىي]", "ي", s)
    s = re.sub(r"[ةه]", "ه", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip().lower()

BLOCK_PATTERNS = [
    r"تجاهل\s+(كل\s+)?التعليمات", r"تجاهل\s+ما\s+سبق",
    r"ignore\s+(all\s+)?previous", r"you\s+are\s+now",
    r"أنت\s+الآن", r"system\s*:", r"developer\s+mode", r"jailbreak",
]
_compiled = [re.compile(p, re.IGNORECASE) for p in BLOCK_PATTERNS]

def check_injection(text):
    if not text or not text.strip(): return False, "المدخل فارغ"
    for p in _compiled:
        if p.search(text): return False, "🚫 محاولة تلاعب مرفوضة"
    if len(text) > 3000: return False, "المدخل طويل جدًا"
    return True, "ok"

def real_sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def count_all():
    total = 0; stats = {}
    if not SOURCES_DIR.exists():
        return 0, {}
    for d in SOURCES_DIR.iterdir():
        if not d.is_dir(): continue
        n = 0
        for f in d.glob("*.json"):
            try: n += len(json.loads(f.read_text(encoding="utf-8")))
            except: pass
        stats[d.name] = n; total += n
    return total, stats

def retrieve(query, k=5):
    items = _load_sources()
    if not items:
        return []
    q_norm = _normalize(query)
    q_words = set(q_norm.split())
    scored = []
    for it in items:
        t_norm = _normalize(it["text"])
        if q_norm in t_norm:
            score = 0.95
        else:
            ratio = SequenceMatcher(None, q_norm, t_norm).ratio()
            t_words = set(t_norm.split())
            common = len(q_words & t_words)
            word_score = common / max(len(q_words), 1) if q_words else 0
            score = max(ratio, word_score * 0.85)
        if score > 0.4:
            scored.append((score, it))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [{**it, "similarity": round(s, 3)} for s, it in scored[:k]]

def verify(query, sources):
    if not sources:
        return {"status":"rejected","confidence":"none","score":0}
    top = sources[0]
    score = top.get("similarity", 0)
    if _normalize(query) in _normalize(top["text"]) or score >= 0.85:
        return {"status":"verified","confidence":"high","score":max(score, 0.9)}
    if score >= 0.55:
        return {"status":"checkable","confidence":"medium","score":score}
    return {"status":"human_review","confidence":"low","score":score}

FQ_KEYS = ["ميراث","تركة","زكاة","فروض","ورثة","نصيب","إرث"]
def is_fiqh(q): return any(k in q for k in FQ_KEYS)

def solve_fiqh(q):
    m = re.search(r"(\d[\d,\.]*)\s*(ريال|دولار|درهم|دينار)", q)
    if "زكاة" in q and m:
        amt = float(m.group(1).replace(",",""))
        return {"answer": f"### 🧮 حساب الزكاة\n\n- المبلغ: **{amt:,.2f} {m.group(2)}**\n- الزكاة (2.5%): **{amt*0.025:,.2f} {m.group(2)}**", "confidence": "deterministic"}
    if "ميراث" in q or "تركة" in q:
        return {"answer": "### 🧮 حساب الميراث\n\nلحساب دقيق أحتاج:\n1. قائمة الورثة\n2. قيمة التركة\n3. الديون والوصايا", "confidence": "deterministic"}
    return None

def refer():
    return ("⚠️ **لم أجد مرجعًا كافيًا**\n\nيُنصح بالرجوع إلى:\n- [اللجنة الدائمة للإفتاء](https://www.alifta.gov.sa)\n- [المجمع الفقهي](https://www.fiqhacademy.org.sa)\n- [الإسلام سؤال وجواب](https://islamqa.info/ar)")

def _last_hash():
    if not AUDIT_FILE.exists(): return "GENESIS"
    lines = [l for l in AUDIT_FILE.read_text(encoding="utf-8").strip().split("\n") if l]
    if not lines: return "GENESIS"
    try: return json.loads(lines[-1])["current_hash"]
    except: return "GENESIS"

def audit_log(qid, query, agents, sources, result, conf):
    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    prev = _last_hash()
    payload = {"query_id": qid, "query_hash": real_sha256(query)[:16], "timestamp": datetime.utcnow().isoformat()+"Z", "agents": agents, "sources_count": len(sources), "result": str(result)[:100], "confidence": conf}
    cur = hashlib.sha256((json.dumps(payload, sort_keys=True, ensure_ascii=False) + prev).encode()).hexdigest()
    with open(AUDIT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps({**payload, "previous_hash": prev, "current_hash": cur}, ensure_ascii=False)+"\n")
    return cur

def read_audit(limit=50):
    if not AUDIT_FILE.exists(): return []
    out = []
    for line in AUDIT_FILE.read_text(encoding="utf-8").strip().split("\n")[-limit:]:
        if line:
            try: out.append(json.loads(line))
            except: pass
    return out

def run_query(query):
    qid = f"q_{uuid.uuid4().hex[:10]}"
    agents = []
    if is_fiqh(query):
        agents.append("fiqh")
        fq = solve_fiqh(query)
        if fq:
            h = audit_log(qid, query, agents, [], fq["answer"], fq["confidence"])
            return {"query_id": qid, "answer": fq["answer"], "sources": [], "confidence": fq["confidence"], "agents": agents, "audit_hash": h}
    agents.append("retriever")
    sources = retrieve(query, k=5)
    agents.append("verification")
    verdict = verify(query, sources)
    if verdict["status"] in ("rejected", "human_review"):
        agents.append("referral")
        answer = refer()
    else:
        status = "موثّق" if verdict["status"] == "verified" else "قابل للتحقق"
        answer = f"✅ **{status}** (ثقة {int(verdict['score']*100)}%)"
    h = audit_log(qid, query, agents, sources, answer, verdict["confidence"])
    return {"query_id": qid, "answer": answer, "sources": sources, "confidence": verdict["confidence"], "agents": agents, "audit_hash": h}

def add_source(category, name, data_list):
    cat_dir = SOURCES_DIR / category
    cat_dir.mkdir(parents=True, exist_ok=True)
    for i, it in enumerate(data_list):
        if "text" not in it: raise ValueError(f"العنصر {i} ينقصه text")
        if "id" not in it: it["id"] = f"{category}_{name}_{i}"
    (cat_dir / f"{name}.json").write_text(json.dumps(data_list, ensure_ascii=False, indent=2), encoding="utf-8")
    global _CACHE; _CACHE = None
    return {"count": len(data_list), "sha": real_sha256(json.dumps(data_list, ensure_ascii=False))}

def add_single_source(category, title, text, reference, trust):
    import time
    name = f"manual_{int(time.time())}"
    item = {"id": f"{category}_{name}", "text": text, "title": title, "book": reference, "number": "", "trust": trust}
    cat_dir = SOURCES_DIR / category
    cat_dir.mkdir(parents=True, exist_ok=True)
    (cat_dir / f"{name}.json").write_text(json.dumps([item], ensure_ascii=False, indent=2), encoding="utf-8")
    global _CACHE; _CACHE = None
    return {"count": 1, "sha": real_sha256(text)}

def list_sources(category=None):
    out = []
    if not SOURCES_DIR.exists(): return out
    for d in SOURCES_DIR.iterdir():
        if not d.is_dir(): continue
        if category and category != d.name: continue
        for f in sorted(d.glob("*.json")):
            try:
                for it in json.loads(f.read_text(encoding="utf-8")):
                    out.append({"id": it.get("id"), "title": it.get("title") or it.get("book", "") or it.get("id"), "text": str(it.get("text", ""))[:200], "book": it.get("book", ""), "number": it.get("number", ""), "category": d.name, "file": f.name, "sha": real_sha256(str(it.get("text", "")))[:16], "trust": it.get("trust", "صحيح")})
            except: pass
    return out

def delete_source(source_id):
    if not SOURCES_DIR.exists(): return False
    for d in SOURCES_DIR.iterdir():
        if not d.is_dir(): continue
        for f in d.glob("*.json"):
            try:
                items = json.loads(f.read_text(encoding="utf-8"))
                new = [it for it in items if it.get("id") != source_id]
                if len(new) != len(items):
                    if new: f.write_text(json.dumps(new, ensure_ascii=False, indent=2), encoding="utf-8")
                    else: f.unlink()
                    global _CACHE; _CACHE = None
                    return True
            except: pass
    return False

def reindex_all():
    global _CACHE; _CACHE = None
    total, stats = count_all()
    return total, stats