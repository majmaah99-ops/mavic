"""MAVIC agents - بحث نصي ذكي بدون ChromaDB"""
import hashlib, json, re, uuid
from datetime import datetime
from pathlib import Path
from difflib import SequenceMatcher

ROOT = Path(__file__).parent.parent
AUDIT_FILE = ROOT / "data" / "audit.jsonl"
SOURCES_DIR = ROOT / "sources"

_CACHE = None

# ============================================
# تحميل المصادر في الذاكرة
# ============================================
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

# ============================================
# تطبيع النص العربي
# ============================================
def _normalize(s):
    """إزالة التشكيل وتوحيد الحروف"""
    s = re.sub(r"[\u064B-\u0652\u0670\u0640]", "", s)  # التشكيل
    s = re.sub(r"[إأآا]", "ا", s)
    s = re.sub(r"[ىي]", "ي", s)
    s = re.sub(r"[ةه]", "ه", s)
    s = re.sub(r"[^\u0600-\u06FF\s]", " ", s)  # إزالة الرموز
    s = re.sub(r"\s+", " ", s)
    return s.strip().lower()

def _words(s):
    """استخراج كلمات ذات معنى (3+ أحرف)"""
    return [w for w in _normalize(s).split() if len(w) >= 3]

# ============================================
# الحماية من Prompt Injection
# ============================================
BLOCK_PATTERNS = [
    r"تجاهل\s+(كل\s+)?التعليمات",
    r"تجاهل\s+ما\s+سبق",
    r"ignore\s+(all\s+)?previous",
    r"you\s+are\s+now",
    r"أنت\s+الآن",
    r"system\s*:",
    r"developer\s+mode",
    r"jailbreak",
    r"اكتب\s+فتوى\s+بجواز",
]
_compiled = [re.compile(p, re.IGNORECASE) for p in BLOCK_PATTERNS]

def check_injection(text):
    if not text or not text.strip():
        return False, "المدخل فارغ"
    for p in _compiled:
        if p.search(text):
            return False, "🚫 محاولة تلاعب مرفوضة"
    if len(text) > 3000:
        return False, "المدخل طويل جدًا"
    return True, "ok"

def real_sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

# ============================================
# عدّ المصادر
# ============================================
def count_all():
    total = 0
    stats = {}
    if not SOURCES_DIR.exists():
        return 0, {}
    for d in SOURCES_DIR.iterdir():
        if not d.is_dir():
            continue
        n = 0
        for f in d.glob("*.json"):
            try:
                n += len(json.loads(f.read_text(encoding="utf-8")))
            except:
                pass
        stats[d.name] = n
        total += n
    return total, stats

# ============================================
# البحث الذكي (محسّن)
# ============================================
def retrieve(query, k=5):
    """
    بحث نصي ذكي:
    - يتجاهل الكلمات القصيرة (أقل من 3 أحرف)
    - يستخدم مطابقة كاملة + مطابقة كلمات
    - عتبات صارمة لمنع النتائج الخاطئة
    """
    items = _load_sources()
    if not items:
        return []

    q_norm = _normalize(query)
    q_words = _words(query)  # كلمات ذات معنى فقط
    q_word_set = set(q_words)
    q_word_count = len(q_words)

    # إذا كان الاستعلام قصيرًا جدًا، ارفض البحث
    if q_word_count == 0:
        return []

    # إذا كان الاستعلام كلمة واحدة قصيرة (3-4 أحرف)، ارفض
    if q_word_count == 1 and len(q_words[0]) < 5:
        return []

    scored = []

    for it in items:
        t_norm = _normalize(it["text"])
        t_words = set(_words(it["text"]))

        # 1) مطابقة مباشرة كاملة (فقط للاستعلامات الطويلة 3+ كلمات)
        direct_match = False
        if q_word_count >= 3 and len(q_norm) >= 15 and q_norm in t_norm:
            direct_match = True

        # 2) حساب النقاط
        if direct_match:
            score = 0.95
        else:
            # مطابقة الكلمات المشتركة (Jaccard-like)
            common = q_word_set & t_words
            if q_word_count > 0:
                overlap_ratio = len(common) / q_word_count
            else:
                overlap_ratio = 0

            # نسبة SequenceMatcher (للمطابقة الجزئية)
            seq_ratio = SequenceMatcher(None, q_norm, t_norm).ratio()

            # مطابقة الكلمات المتتالية (phrase match) — أقوى من الكلمات المتفرقة
            phrase_bonus = 0
            if q_word_count >= 2:
                # ابحث عن كلمتين متتاليتين من الاستعلام في النص
                for i in range(len(q_words) - 1):
                    phrase = f"{q_words[i]} {q_words[i+1]}"
                    if phrase in t_norm:
                        phrase_bonus = 0.15
                        break

            # الدمج: نعتمد على تكرار الكلمات أكثر من SequenceMatcher
            word_based = overlap_ratio * 0.85 + phrase_bonus
            score = max(word_based, seq_ratio * 0.6)

            # عقوبة إذا كانت المطابقة ضعيفة
            if overlap_ratio < 0.4:
                score *= 0.5
            if overlap_ratio < 0.2:
                score *= 0.3

        if score > 0.45:
            scored.append((score, it))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [{**it, "similarity": round(s, 3)} for s, it in scored[:k]]

# ============================================
# التحقق
# ============================================
def verify(query, sources):
    """
    تصنيف النتيجة:
    - verified: مطابقة عالية (95%+)
    - checkable: مطابقة متوسطة
    - human_review: مطابقة ضعيفة
    - rejected: لا نتيجة
    """
    if not sources:
        return {"status": "rejected", "confidence": "none", "score": 0}

    top = sources[0]
    score = top.get("similarity", 0)
    q_norm = _normalize(query)
    t_norm = _normalize(top["text"])
    q_words = _words(query)

    # مطابقة مباشرة فقط إذا كان الاستعلام طويلًا
    direct_match = (
        len(q_words) >= 3
        and len(q_norm) >= 15
        and q_norm in t_norm
    )

    if direct_match:
        return {"status": "verified", "confidence": "high", "score": 0.95}
    if score >= 0.88:
        return {"status": "verified", "confidence": "high", "score": score}
    if score >= 0.65:
        return {"status": "checkable", "confidence": "medium", "score": score}
    return {"status": "human_review", "confidence": "low", "score": score}

# ============================================
# وكيل الفقه
# ============================================
FQ_KEYS = ["ميراث", "تركة", "زكاة", "فروض", "ورثة", "نصيب", "إرث"]

def is_fiqh(q):
    return any(k in q for k in FQ_KEYS)

def solve_fiqh(q):
    m = re.search(r"(\d[\d,\.]*)\s*(ريال|دولار|درهم|دينار|جنيه)", q)
    if "زكاة" in q and m:
        amt = float(m.group(1).replace(",", ""))
        return {
            "answer": (
                f"### 🧮 حساب الزكاة (حتمي)\n\n"
                f"- **المبلغ**: {amt:,.2f} {m.group(2)}\n"
                f"- **النصاب**: يُراجع شرعيًا (نصاب الذهب/الفضة)\n"
                f"- **الزكاة المستحقة** (2.5%): **{amt * 0.025:,.2f} {m.group(2)}**\n\n"
                f"> ⚠️ هذا حساب تقديري، يُراجع مع المختص."
            ),
            "confidence": "deterministic"
        }
    if "ميراث" in q or "تركة" in q:
        return {
            "answer": (
                "### 🧮 حساب الميراث\n\n"
                "لإتمام الحساب بدقة أحتاج:\n"
                "1. **قائمة الورثة** (زوج/زوجة، أبناء، بنات، أب، أم...)\n"
                "2. **قيمة التركة الإجمالية**\n"
                "3. **الديون والوصايا** (إن وُجدت)\n\n"
                "📌 يرجى إعادة الإدخال بالتفاصيل، أو مراجعة مختص."
            ),
            "confidence": "deterministic"
        }
    return None

# ============================================
# وكيل الإحالة
# ============================================
def refer():
    return (
        "⚠️ **لم أجد مرجعًا كافيًا للتحقق**\n\n"
        "يُنصح بالرجوع إلى:\n"
        "- [اللجنة الدائمة للبحوث العلمية والإفتاء](https://www.alifta.gov.sa)\n"
        "- [المجمع الفقهي الإسلامي](https://www.fiqhacademy.org.sa)\n"
        "- [الإسلام سؤال وجواب](https://islamqa.info/ar)\n"
        "- [دار الإفتاء المصرية](https://www.dar-alifta.org)"
    )

# ============================================
# سجل التدقيق (Hash Chain)
# ============================================
def _last_hash():
    if not AUDIT_FILE.exists():
        return "GENESIS"
    lines = [l for l in AUDIT_FILE.read_text(encoding="utf-8").strip().split("\n") if l]
    if not lines:
        return "GENESIS"
    try:
        return json.loads(lines[-1])["current_hash"]
    except:
        return "GENESIS"

def audit_log(qid, query, agents, sources, result, conf):
    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    prev = _last_hash()
    payload = {
        "query_id": qid,
        "query_hash": real_sha256(query)[:16],
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "agents": agents,
        "sources_count": len(sources),
        "result": str(result)[:100],
        "confidence": conf,
    }
    cur = hashlib.sha256(
        (json.dumps(payload, sort_keys=True, ensure_ascii=False) + prev).encode()
    ).hexdigest()
    with open(AUDIT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps({**payload, "previous_hash": prev, "current_hash": cur}, ensure_ascii=False) + "\n")
    return cur

def read_audit(limit=50):
    if not AUDIT_FILE.exists():
        return []
    out = []
    for line in AUDIT_FILE.read_text(encoding="utf-8").strip().split("\n")[-limit:]:
        if line:
            try:
                out.append(json.loads(line))
            except:
                pass
    return out

# ============================================
# المنسّق (Orchestrator)
# ============================================
def run_query(query):
    qid = f"q_{uuid.uuid4().hex[:10]}"
    agents = []

    # 1) سؤال فقهي حسابي؟
    if is_fiqh(query):
        agents.append("fiqh")
        fq = solve_fiqh(query)
        if fq:
            h = audit_log(qid, query, agents, [], fq["answer"], fq["confidence"])
            return {
                "query_id": qid,
                "answer": fq["answer"],
                "sources": [],
                "confidence": fq["confidence"],
                "agents": agents,
                "audit_hash": h,
            }

    # 2) استرجاع
    agents.append("retriever")
    sources = retrieve(query, k=5)

    # 3) تحقق
    agents.append("verification")
    verdict = verify(query, sources)

    # 4) إحالة أو إجابة
    if verdict["status"] in ("rejected", "human_review"):
        agents.append("referral")
        answer = refer()
    else:
        status_text = "موثّق" if verdict["status"] == "verified" else "قابل للتحقق"
        answer = f"✅ **{status_text}** (ثقة {int(verdict['score'] * 100)}%)"

    h = audit_log(qid, query, agents, sources, answer, verdict["confidence"])
    return {
        "query_id": qid,
        "answer": answer,
        "sources": sources,
        "confidence": verdict["confidence"],
        "agents": agents,
        "audit_hash": h,
    }

# ============================================
# إدارة المصادر (Admin)
# ============================================
def add_source(category, name, data_list):
    cat_dir = SOURCES_DIR / category
    cat_dir.mkdir(parents=True, exist_ok=True)
    for i, it in enumerate(data_list):
        if "text" not in it:
            raise ValueError(f"العنصر {i} ينقصه text")
        if "id" not in it:
            it["id"] = f"{category}_{name}_{i}"
    (cat_dir / f"{name}.json").write_text(
        json.dumps(data_list, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    global _CACHE
    _CACHE = None
    return {
        "count": len(data_list),
        "sha": real_sha256(json.dumps(data_list, ensure_ascii=False)),
    }

def add_single_source(category, title, text, reference, trust):
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
    (cat_dir / f"{name}.json").write_text(
        json.dumps([item], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    global _CACHE
    _CACHE = None
    return {"count": 1, "sha": real_sha256(text)}

def list_sources(category=None):
    out = []
    if not SOURCES_DIR.exists():
        return out
    for d in SOURCES_DIR.iterdir():
        if not d.is_dir():
            continue
        if category and category != d.name:
            continue
        for f in sorted(d.glob("*.json")):
            try:
                for it in json.loads(f.read_text(encoding="utf-8")):
                    out.append({
                        "id": it.get("id"),
                        "title": it.get("title") or it.get("book", "") or it.get("id"),
                        "text": str(it.get("text", ""))[:200],
                        "book": it.get("book", ""),
                        "number": it.get("number", ""),
                        "category": d.name,
                        "file": f.name,
                        "sha": real_sha256(str(it.get("text", "")))[:16],
                        "trust": it.get("trust", "صحيح"),
                    })
            except:
                pass
    return out

def delete_source(source_id):
    if not SOURCES_DIR.exists():
        return False
    for d in SOURCES_DIR.iterdir():
        if not d.is_dir():
            continue
        for f in d.glob("*.json"):
            try:
                items = json.loads(f.read_text(encoding="utf-8"))
                new = [it for it in items if it.get("id") != source_id]
                if len(new) != len(items):
                    if new:
                        f.write_text(json.dumps(new, ensure_ascii=False, indent=2), encoding="utf-8")
                    else:
                        f.unlink()
                    global _CACHE
                    _CACHE = None
                    return True
            except:
                pass
    return False

def reindex_all():
    """متوافق مع الكود القديم - لا نحتاجه الآن لكنه مُبقى"""
    global _CACHE
    _CACHE = None
    total, stats = count_all()
    return total, stats