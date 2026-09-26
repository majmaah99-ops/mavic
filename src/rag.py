"""قاعدة المصادر والبحث الدلالي الذكي"""
import re


# ===== كلمات التوقف العربية (تُستبعد من البحث) =====
STOP_WORDS = {
    "ما", "من", "في", "على", "إلى", "عن", "هذا", "هذه", "ذلك", "تلك",
    "التي", "الذي", "الذين", "اللاتي", "اللواتي", "إن", "أن", "كان",
    "كانت", "يكون", "تكون", "هو", "هي", "هم", "هن", "أنا", "أنت",
    "نحن", "أنتم", "هل", "كيف", "لماذا", "متى", "أين", "كم", "أي",
    "و", "أو", "ثم", "لكن", "بل", "لا", "لم", "لن", "قد", "كل",
    "بعض", "غير", "بين", "مع", "عند", "قبل", "بعد", "يا", "أيها",
    "اذكر", "أعطني", "قل", "أخبرني", "حدثني", "وضح", "اشرح",
}


SEED_SOURCES = [
    {
        "source_id": "quran_2_255",
        "text": "اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ ۚ لَا تَأْخُذُهُ سِنَةٌ وَلَا نَوْمٌ",
        "reference": "سورة البقرة، الآية 255 (آية الكرسي)",
        "source_type": "quran",
        "authenticity": "قطعي الثبوت",
        "topics": ["الله", "توحيد", "قرآن", "آية الكرسي", "عقيدة"],
    },
    {
        "source_id": "quran_103_1",
        "text": "وَالْعَصْرِ إِنَّ الْإِنْسَانَ لَفِي خُسْرٍ إِلَّا الَّذِينَ آمَنُوا وَعَمِلُوا الصَّالِحَاتِ",
        "reference": "سورة العصر",
        "source_type": "quran",
        "authenticity": "قطعي الثبوت",
        "topics": ["صبر", "إيمان", "عمل صالح", "حق"],
    },
    {
        "source_id": "bukhari_1",
        "text": "إنما الأعمال بالنيات، وإنما لكل امرئ ما نوى، فمن كانت هجرته إلى الله ورسوله فهجرته إلى الله ورسوله",
        "reference": "صحيح البخاري، حديث رقم 1",
        "source_type": "hadith",
        "authenticity": "صحيح",
        "topics": ["نية", "نيات", "أعمال", "إخلاص", "هجرة"],
    },
    {
        "source_id": "bukhari_8",
        "text": "بني الإسلام على خمس: شهادة أن لا إله إلا الله وأن محمداً رسول الله، وإقام الصلاة، وإيتاء الزكاة، وحج البيت، وصوم رمضان",
        "reference": "صحيح البخاري، حديث رقم 8",
        "source_type": "hadith",
        "authenticity": "صحيح",
        "topics": ["أركان الإسلام", "شهادة", "إسلام", "خمس"],
    },
    {
        "source_id": "muslim_2553",
        "text": "البر حسن الخلق، والإثم ما حاك في نفسك وكرهت أن يطلع عليه الناس",
        "reference": "صحيح مسلم، حديث رقم 2553",
        "source_type": "hadith",
        "authenticity": "صحيح",
        "topics": ["بر", "خلق", "أخلاق", "إثم"],
    },
    {
        "source_id": "fiqh_zakat",
        "text": "نصاب الذهب عشرون مثقالاً، ومقدار زكاة النقود ربع العشر (2.5%) إذا بلغت النصاب وحال عليها الحول",
        "reference": "موسوعة الفقه الإسلامي، باب الزكاة",
        "source_type": "fiqh",
        "authenticity": "معتمد",
        "topics": ["زكاة", "نصاب", "ذهب", "نقود", "مال"],
    },
    {
        "source_id": "fiqh_witr",
        "text": "صلاة الوتر سنة مؤكدة، ووقتها بعد صلاة العشاء إلى طلوع الفجر، وأقلها ركعة واحدة، وأكثرها إحدى عشرة ركعة",
        "reference": "موسوعة الفقه الإسلامي، باب صلاة التطوع",
        "source_type": "fiqh",
        "authenticity": "معتمد",
        "topics": ["صلاة", "وتر", "سنة", "قيام الليل", "تطوع"],
    },
    {
        "source_id": "fiqh_salah",
        "text": "الصلوات الخمس المفروضة: الفجر، الظهر، العصر، المغرب، العشاء. وهي فرض عين على كل مسلم بالغ عاقل",
        "reference": "موسوعة الفقه الإسلامي، باب الصلوات المفروضة",
        "source_type": "fiqh",
        "authenticity": "معتمد",
        "topics": ["صلاة", "فريضة", "فرض", "صلوات", "مكتوبة"],
    },
    {
        "source_id": "fiqh_sawm",
        "text": "صوم رمضان فرض عين على كل مسلم بالغ عاقل قادر، ووقته من طلوع الفجر إلى غروب الشمس",
        "reference": "موسوعة الفقه الإسلامي، باب الصيام",
        "source_type": "fiqh",
        "authenticity": "معتمد",
        "topics": ["صوم", "صيام", "رمضان", "فريضة"],
    },
    {
        "source_id": "fiqh_hajj",
        "text": "الحج فرض مرة واحدة في العمر على المستطيع، وأركانه: الإحرام، والطواف، والسعي، والوقوف بعرفة",
        "reference": "موسوعة الفقه الإسلامي، باب الحج",
        "source_type": "fiqh",
        "authenticity": "معتمد",
        "topics": ["حج", "عمرة", "فريضة", "أركان", "مستطيع"],
    },
]


def _normalize(text):
    """تطبيع النص: إزالة التشكيل وتوحيد الحروف"""
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
    text = re.sub(r"[^\w\s\u0600-\u06FF]", " ", text)
    text = re.sub(r"[إأآا]", "ا", text)
    text = re.sub(r"[ىي]", "ي", text)
    text = re.sub(r"ة", "ه", text)
    return text.lower().strip()


def _keywords(text):
    """استخراج الكلمات المفتاحية (بدون كلمات التوقف)"""
    words = _normalize(text).split()
    return set(w for w in words if len(w) > 2 and w not in STOP_WORDS)


def search_sources(query, top_k=5):
    """
    بحث محسّن:
    1. استبعاد كلمات التوقف
    2. اشتراط تطابق كلمات مفتاحية حقيقية
    3. ترجيح المواضيع (topics)
    4. رفض المصادر ضعيفة الصلة
    """
    q_keywords = _keywords(query)
    q_norm = _normalize(query)

    if not q_keywords:
        return []

    is_fiqh_question = any(k in q_norm for k in [
        "حكم", "يجوز", "حرام", "حلال", "فرض", "سنه", "واجب", "مكروه", "مباح"
    ])

    results = []
    for src in SEED_SOURCES:
        src_keywords = _keywords(src["text"] + " " + src["reference"])

        # 1) تطابق الكلمات المفتاحية الدقيقة
        exact_matches = q_keywords & src_keywords
        exact_score = len(exact_matches) * 3.0

        # 2) مطابقة المواضيع
        topic_matches = 0
        matched_topics = []
        for topic in src.get("topics", []):
            t_norm = _normalize(topic)
            for qk in q_keywords:
                if t_norm == qk or t_norm in qk or qk in t_norm:
                    topic_matches += 1
                    matched_topics.append(topic)
                    break
        topic_score = topic_matches * 4.0

        # 3) مطابقة نصية دقيقة في النص الكامل
        src_norm = _normalize(src["text"] + " " + src["reference"])
        substring_score = 0
        for qk in q_keywords:
            if qk not in exact_matches and qk in src_norm:
                substring_score += 1.0

        # 4) مكافأة للمصادر الفقهية عند السؤال عن حكم
        fiqh_bonus = 2.0 if (is_fiqh_question and src["source_type"] == "fiqh") else 0

        total_score = exact_score + topic_score + substring_score + fiqh_bonus

        # شروط القبول: يحتاج على الأقل تطابق كلمة مفتاحية واحدة أو موضوع واحد
        if total_score >= 3.0:
            results.append({**src, "_score": total_score, "_matched_topics": matched_topics})

    results.sort(key=lambda x: x["_score"], reverse=True)

    # حساب similarity نسبي
    if results:
        max_score = max(r["_score"] for r in results)
        for r in results:
            r["similarity"] = round(min(r["_score"] / max(max_score, 1), 1.0), 2)

    for r in results:
        r.pop("_score", None)
        r.pop("_matched_topics", None)

    return results[:top_k]


def source_count():
    return len(SEED_SOURCES)
