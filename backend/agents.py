"""الوكلاء الأربعة + الأمان + Audit"""
import hashlib, json, re, os, uuid
from datetime import datetime
from pathlib import Path
from difflib import SequenceMatcher

ROOT = Path(__file__).parent.parent
AUDIT_FILE = ROOT / "data" / "audit.jsonl"
SOURCES_DIR = ROOT / "sources"
CHROMA_PATH = str(ROOT / "data" / "chroma")

# ---------------- Security ----------------
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

# ---------------- SHA-256 ----------------
def real_sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

# ---------------- Retriever (ChromaDB) ----------------
_client = None
_collection = None

def _init_chroma():
    global _client, _collection
    if _client: return
    import chromadb
    from chromadb.utils import embedding_functions
    _client = chromadb.PersistentClient(path=CHROMA_PATH)
    embed = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    _collection = _client.get_or_create_collection("mavic", embedding_function=embed)

def retrieve(query, k=5):
    _init_chroma()
    try:
        res = _collection.query(query_texts=[query], n_results=k)
    except: return []
    out = []
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    dists = res.get("distances", [[]])[0]
    for d, m, s in zip(docs, metas, dists):
        out.append({
            "text": d, "source_id": m.get("source_id",""),
            "book": m.get("book",""), "number": m.get("number",""),
            "category": m.get("category",""), "sha": m.get("sha",""),
            "similarity": round(1 - s, 3),
        })
    return out

def reindex_all():
    _init_chroma()
    # حذف الكل
    try:
        total = _collection.count()
        if total:
            ids = _collection.get()["ids"]
            for i in range(0, len(ids), 500):
                _collection.delete(ids=ids[i:i+500])
    except: pass

    all_items = []
    stats = {}
    for cat_dir in SOURCES_DIR.iterdir():
        if not cat_dir.is_dir(): continue
        count = 0
        for f in sorted(cat_dir.glob("*.json")):
            try:
                items = json.loads(f.read_text(encoding="utf-8"))
                for it in items:
                    it["_cat"] = cat_dir.name
                    it["_file"] = f.name
                all_items.extend(items)
                count += len(items)
            except: pass
        stats[cat_dir.name] = count

    if not all_items: return 0, stats

    for i in range(0, len(all_items), 200):
        batch = all_items[i:i+200]
        _collection.add(
            ids=[str(it.get("id", f"x{i+j}")) for j, it in enumerate(batch)],
            documents=[str(it.get("text","")) for it in batch],
            metadatas=[{
                "source_id": str(it.get("id","")),
                "book": str(it.get("book",""))[:200],
                "number": str(it.get("number",""))[:50],
                "category": it.get("_cat",""),
                "file": it.get("_file",""),
                "sha": real_sha256(str(it.get("text","")))[:16],
            } for it in batch],
        )
    return len(all_items), stats

def count_all():
    total = 0
    stats = {}
    for d in SOURCES_DIR.iterdir():
        if not d.is_dir(): continue
        n = 0
        for f in d.glob("*.json"):
            try: n += len(json.loads(f.read_text(encoding="utf-8")))
            except: pass
        stats[d.name] = n
        total += n
    return total, stats

# ---------------- Verifier ----------------
def verify(query, sources):
    if not sources:
        return {"status":"rejected","confidence":"none"}
    top = sources[0]
    direct = SequenceMatcher(None, query.replace(" ",""), top["text"].replace(" ","")).ratio()
    score = max(direct, top.get("similarity", 0))
    if score >= 0.85: return {"status":"verified","confidence":"high","score":score}
    if score >= 0.60: return {"status":"checkable","confidence":"medium","score":score}
    return {"status":"human_review","confidence":"low","score":score}

# ---------------- Fiqh ----------------
FQ_KEYS = ["ميراث","تركة","زكاة","فروض","ورثة","نصيب","إرث"]
def is_fiqh(q): return any(k in q for k in FQ_KEYS)

def solve_fiqh(q):
    m = re.search(r"(\d[\d,\.]*)\s*(ريال|دولار|درهم|دينار)", q)
    if "زكاة" in q and m:
        amt = float(m.group(1).replace(",",""))
        return {"answer": f"### 🧮 الزكاة\n- المبلغ: {amt:,.2f} {m.group(2)}\n- الزكاة (2.5%): **{amt*0.025:,.2f} {m.group(2)}**", "confidence":"deterministic"}
    return None

# ---------------- Referral ----------------
def refer():
    return "⚠️ لا يمكن التحقق. يُنصح بالرجوع إلى:\n- [اللجنة الدائمة للإفتاء](https://www.alifta.gov.sa)\n- [المجمع الفقهي](https://www.fiqhacademy.org.sa)\n- [الإسلام سؤال وجواب](https://islamqa.info/ar)"

# ---------------- Audit ----------------
def _last_hash():
    if not AUDIT_FILE.exists(): return "GENESIS"
    lines = [l for l in AUDIT_FILE.read_text(encoding="utf-8").strip().split("\n") if l]
    if not lines: return "GENESIS"
    try: return json.loads(lines[-1])["current_hash"]
    except: return "GENESIS"

def audit_log(qid, query, agents, sources, result, conf):
    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    prev = _last_hash()
    payload = {
        "query_id": qid, "query_hash": real_sha256(query)[:16],
        "timestamp": datetime.utcnow().isoformat()+"Z",
        "agents": agents, "sources_count": len(sources),
        "result": str(result)[:100], "confidence": conf,
    }
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

# ---------------- Orchestrator ----------------
def run_query(query):
    qid = f"q_{uuid.uuid4().hex[:10]}"
    agents = []
    
    if is_fiqh(query):
        agents.append("fiqh")
        fq = solve_fiqh(query)
        if fq:
            h = audit_log(qid, query, agents, [], fq["answer"], fq["confidence"])
            return {"query_id": qid, "answer": fq["answer"], "sources": [],
                    "confidence": fq["confidence"], "agents": agents, "audit_hash": h}
    
    agents.append("retriever")
    sources = retrieve(query, k=5)
    agents.append("verification")
    verdict = verify(query, sources)
    
    if verdict["status"] in ("rejected","human_review"):
        agents.append("referral")
        answer = refer()
    else:
        answer = verdict.get("status") == "verified" and f"✅ موثّق (ثقة {int(verdict['score']*100)}%)" or f"⚠️ قابل للتحقق (ثقة {int(verdict['score']*100)}%)"
    
    h = audit_log(qid, query, agents, sources, answer, verdict["confidence"])
    return {"query_id": qid, "answer": answer, "sources": sources,
            "confidence": verdict["confidence"], "agents": agents, "audit_hash": h}

# ---------------- Add Source ----------------
def add_source(category, name, data_list):
    """يضيف مصدر ويعيد SHA-256"""
    cat_dir = SOURCES_DIR / category
    cat_dir.mkdir(parents=True, exist_ok=True)
    target = cat_dir / f"{name}.json"
    
    # تحقق
    for i, it in enumerate(data_list):
        if "text" not in it:
            raise ValueError(f"العنصر {i} ينقصه text")
        if "id" not in it:
            it["id"] = f"{category}_{name}_{i}"
    
    target.write_text(json.dumps(data_list, ensure_ascii=False, indent=2), encoding="utf-8")
    sha = real_sha256(json.dumps(data_list, ensure_ascii=False))
    return {"count": len(data_list), "file": str(target.relative_to(ROOT)), "sha": sha}

def add_single_source(category, title, text, reference, trust):
    """يضيف مصدر واحد من النموذج"""
    import time
    name = f"manual_{int(time.time())}"
    item = {
        "id": f"{category}_{name}",
        "text": text,
        "title": title,
        "book": reference,
        "number": "",
        "trust": trust,
    }
    cat_dir = SOURCES_DIR / category
    cat_dir.mkdir(parents=True, exist_ok=True)
    f = cat_dir / f"{name}.json"
    f.write_text(json.dumps([item], ensure_ascii=False, indent=2), encoding="utf-8")
    return {"count": 1, "file": str(f.relative_to(ROOT)), "sha": real_sha256(text), "id": item["id"]}

def list_sources(category=None):
    """يعيد قائمة بكل المصادر للإدارة"""
    out = []
    for d in SOURCES_DIR.iterdir():
        if not d.is_dir(): continue
        if category and category != d.name: continue
        for f in sorted(d.glob("*.json")):
            try:
                items = json.loads(f.read_text(encoding="utf-8"))
                for it in items:
                    out.append({
                        "id": it.get("id"),
                        "title": it.get("title") or it.get("book","") or it.get("id"),
                        "text": str(it.get("text",""))[:200],
                        "book": it.get("book",""),
                        "number": it.get("number",""),
                        "category": d.name,
                        "file": f.name,
                        "sha": real_sha256(str(it.get("text","")))[:16],
                        "trust": it.get("trust","صحيح"),
                    })
            except: pass
    return out

def delete_source(source_id):
    """يحذف مصدرًا بالـ id"""
    for d in SOURCES_DIR.iterdir():
        if not d.is_dir(): continue
        for f in d.glob("*.json"):
            try:
                items = json.loads(f.read_text(encoding="utf-8"))
                new_items = [it for it in items if it.get("id") != source_id]
                if len(new_items) != len(items):
                    if new_items:
                        f.write_text(json.dumps(new_items, ensure_ascii=False, indent=2), encoding="utf-8")
                    else:
                        f.unlink()
                    return True
            except: pass
    return False
