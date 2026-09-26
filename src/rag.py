"""قاعدة المصادر والبحث الذكي"""
import re
import sqlite3
from pathlib import Path


DB_PATH = Path("data/hadith.db")


STOP_WORDS = {
    "ما", "من", "في", "على", "إلى", "عن", "هذا", "هذه", "ذلك", "تلك",
    "التي", "الذي", "الذين", "إن", "أن", "كان", "كانت", "يكون",
    "هو", "هي", "هم", "هن", "أنا", "أنت", "نحن", "أنتم",
    "هل", "كيف", "لماذا", "متى", "أين", "كم", "أي",
    "و", "أو", "ثم", "لكن", "بل", "لا", "لم", "لن", "قد", "كل",
    "بعض", "غير", "بين", "مع", "عند", "قبل", "بعد",
    "اذكر", "أعطني", "قل", "أخبرني", "حدثني", "وضح", "اشرح",
}


SEED_SOURCES = [
    {
        "source_id": "quran_2_255",
        "text": "اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ ۚ لَا تَأْخُذُهُ سِنَةٌ وَلَا نَوْمٌ",
        "reference": "سورة البقرة، الآية 255 (آية الكرسي)",
        "source_type": "quran",
        "authenticity": "قطعي الثبوت",
        "topics": ["الله", "توحيد", "قرآن", "آية الكرسي"],
    },
    {
        "source_id": "quran_103_1",
        "text": "وَالْعَصْرِ إِنَّ الْإِنْسَانَ لَفِي خُسْرٍ إِلَّا الَّذِينَ آمَنُوا وَعَمِلُوا الصَّالِحَاتِ",
        "reference": "سورة العصر",
        "source_type": "quran",
        "authenticity": "قطعي الثبوت",
        "topics": ["صبر", "إيمان", "عمل صالح"],
    },
    {
        "source_id": "bukhari_1_manual",
        "text": "إنما الأعمال بالنيات، وإنما لكل امرئ ما نوى",
        "reference": "صحيح البخاري، حديث رقم 1 (نسخة مصغرة)",
        "source_type": "hadith",
        "authenticity": "صحيح",
        "topics": ["نية", "نيات", "أعمال", "إخلاص", "هجرة"],
    },
    {
        "source_id": "fiqh_zakat",
        "text": "نصاب الذهب عشرون مثقالاً، ومقدار زكاة النقود ربع العشر (2.5%) إذا بلغت النصاب وحال عليها الحول",
        "reference": "موسوعة الفقه الإسلامي، باب الزكاة",
        "source_type": "fiqh",
        "authenticity": "معتمد",
        "topics": ["زكاة", "نصاب", "ذهب", "نقود"],
    },
    {
        "source_id": "fiqh_witr",
        "text": "صلاة الوتر سنة مؤكدة، ووقتها بعد صلاة العشاء إلى طلوع الفجر، وأقلها ركعة واحدة، وأكثرها إحدى عشرة ركعة",
        "reference": "موسوعة الفقه الإسلامي، باب صلاة التطوع",
        "source_type": "fiqh",
        "authenticity": "معتمد",
        "topics": ["صلاة", "وتر", "سنة", "قيام الليل"],
    },
    {
        "source_id": "fiqh_salah",
        "text": "الصلوات الخمس المفروضة: الفجر، الظهر، العصر، المغرب، العشاء. وهي فرض عين على كل مسلم بالغ عاقل",
        "reference": "موسوعة الفقه الإسلامي، باب الصلوات المفروضة",
        "source_type": "fiqh",
        "authenticity": "معتمد",
        "topics": ["صلاة", "فريضة", "فرض", "صلوات"],
    },
]


def _normalize(text):
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
    text = re.sub(r"[^\w\s\u0600-\u06FF]", " ", text)
    text = re.sub(r"[إأآا]", "ا", text)
    text = re.sub(r"[ىي]", "ي", text)
    text = re.sub(r"ة", "ه", text)
    return text.lower().strip()


def _keywords_normalized(text):
    """كلمات مفتاحية مُطبّعة (للمصادر المحلية)"""
    words = _normalize(text).split()
    return set(w for w in words if len(w) > 2 and w not in STOP_WORDS)


def _keywords_original(text):
    """كلمات مفتاحية أصلية (للبحث في DB)"""
    clean = re.sub(r"[\u064B-\u065F\u0670]", "", text)
    clean = re.sub(r"[^\w\s\u0600-\u06FF]", " ", clean)
    words = clean.split()
    return [w for w in words if len(w) > 2 and w not in STOP_WORDS]


# ===== البحث في المصادر المحلية =====

def search_local_sources(query, top_k=3):
    q_keywords = _keywords_normalized(query)
    q_norm = _normalize(query)

    if not q_keywords:
        return []

    results = []
    for src in SEED_SOURCES:
        src_keywords = _keywords_normalized(src["text"] + " " + src["reference"])
        exact_matches = q_keywords & src_keywords
        exact_score = len(exact_matches) * 3.0

        topic_matches = 0
        for topic in src.get("topics", []):
            t_norm = _normalize(topic)
            for qk in q_keywords:
                if t_norm == qk or t_norm in qk or qk in t_norm:
                    topic_matches += 1
                    break
        topic_score = topic_matches * 4.0

        total_score = exact_score + topic_score
        if total_score >= 3.0:
            results.append({**src, "_score": total_score})

    results.sort(key=lambda x: x["_score"], reverse=True)
    return [{k: v for k, v in r.items() if k != "_score"} for r in results[:top_k]]


# ===== البحث في قاعدة بيانات الأحاديث =====

def search_hadith_db(query, top_k=5):
    """البحث في DB بكلمتين: أصلية + مطبّعة"""
    if not DB_PATH.exists():
        return []

    # نجمع بين الكلمات الأصلية والمطبعة (لضمان المطابقة في كل الحالات)
    kws_original = _keywords_original(query)
    kws_normalized = list(_keywords_normalized(query))

    # نضيف الكلمات الأصلية أولاً (لها أولوية)
    all_keywords = []
    seen_kw = set()
    for kw in kws_original + kws_normalized:
        if kw not in seen_kw and len(kw) > 2:
            seen_kw.add(kw)
            all_keywords.append(kw)

    if not all_keywords:
        return []

    # نرتب الكلمات حسب الطول تنازلياً (الأطول = الأكثر تحديداً)
    all_keywords.sort(key=len, reverse=True)

    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        results = []
        seen_hadith = set()

        for keyword in all_keywords:
            cursor.execute("""
                SELECT book, hadith_number, text, grade
                FROM hadiths
                WHERE text LIKE ?
                LIMIT ?
            """, (f"%{keyword}%", top_k))

            for row in cursor.fetchall():
                book, number, text, grade = row
                key = f"{book}_{number}"
                if key in seen_hadith:
                    continue
                seen_hadith.add(key)
                results.append({
                    "source_id": f"hadith_{book}_{number}",
                    "text": text,
                    "reference": f"{book}، حديث رقم {number}",
                    "source_type": "hadith",
                    "authenticity": grade if grade else "صحيح",
                })
                if len(results) >= top_k:
                    break

            if len(results) >= top_k:
                break

        conn.close()
        return results
    except Exception as e:
        print(f"DB Error: {e}")
        return []


# ===== الدالة الرئيسية =====

def search_sources_enhanced(query, top_k=5):
    """البحث الموحد: محلي + DB + fallback"""
    local_results = search_local_sources(query, top_k=3)
    hadith_results = search_hadith_db(query, top_k=3)

    # إذا لم نجد أي نتيجة، نجرب البحث بكلمة واحدة فقط
    if not local_results and not hadith_results:
        original_kws = _keywords_original(query)
        for kw in original_kws:
            if len(kw) > 3:
                local_results = search_local_sources(kw, top_k=2)
                hadith_results = search_hadith_db(kw, top_k=2)
                if local_results or hadith_results:
                    break

    all_results = local_results + hadith_results
    return all_results[:top_k]


def source_count():
    base = len(SEED_SOURCES)
    if DB_PATH.exists():
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM hadiths")
            hadith_count = cursor.fetchone()[0]
            conn.close()
            return base + hadith_count
        except Exception:
            return base
    return base


def search_sources(query, top_k=5):
    return search_sources_enhanced(query, top_k)
