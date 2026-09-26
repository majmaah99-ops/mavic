"""قاعدة المصادر والبحث الدلالي الذكي"""
import re


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
        "text": "إنما الأعمال بالنيات، وإنما لكل امرئ ما نوى",
        "reference": "صحيح البخاري، حديث رقم 1",
        "source_type": "hadith",
        "authenticity": "صحيح",
        "topics": ["نية", "أعمال", "إخلاص", "هجرة"],
    },
    {
        "source_id": "bukhari_8",
        "text": "بني الإسلام على خمس: شهادة أن لا إله إلا الله وأن محمداً رسول الله، وإقام الصلاة، وإيتاء الزكاة، وحج البيت، وصوم رمضان",
        "reference": "صحيح البخاري، حديث رقم 8",
        "source_type": "hadith",
        "authenticity": "صحيح",
        "topics": ["أركان الإسلام", "شهادة", "صلاة", "زكاة", "حج", "صوم", "إسلام"],
    },
    {
        "source_id": "muslim_2553",
        "text": "البر حسن الخلق، والإثم ما حاك في نفسك وكرهت أن يطلع عليه الناس",
        "reference": "صحيح مسلم، حديث رقم 2553",
        "source_type": "hadith",
        "authenticity": "صحيح",
        "topics": ["بر", "خلق", "إثم", "أخلاق"],
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
        "topics": ["صلاة", "فريضة", "فرض", "صلوات خمس", "مكتوبة"],
    },
    {
        "source_id": "fiqh_sawm",
        "text": "صوم رمضان فرض عين على كل مسلم بالغ عاقل قادر، ووقته من طلوع الفجر إلى غروب الشمس",
        "reference": "موسوعة الفقه الإسلامي، باب الصيام",
        "source_type": "fiqh",
        "authenticity": "معتمد",
        "topics": ["صوم", "رمضان", "فريضة", "صيام"],
    },
    {
        "source_id": "fiqh_hajj",
        "text": "الحج فرض مرة واحدة في العمر على المستطيع، وأركانه: الإحرام، والطواف، والسعي، والوقوف بعرفة",
        "reference": "موسوعة الفقه الإسلامي، باب الحج",
        "source_type": "fiqh",
        "authenticity": "معتمد",
        "topics": ["حج", "فريضة", "أركان", "عمرة", "مستطيع"],
    },
]


def _normalize(text):
    """تطبيع النص: إزالة التشكيل والرموز"""
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)  # إزالة التشكيل
    text = re.sub(r"[^\w\s\u0600-\u06FF]", " ", text)
    text = re.sub(r"[إأآا]", "ا", text)  # توحيد الألف
    text = re.sub(r"[ىي]", "ي", text)  # توحيد الياء
    text = re.sub(r"ة", "ه", text)  # توحيد التاء المربوطة
    return text.lower().strip()


def search_sources(query, top_k=5):
    """
    بحث محسّن يعتمد على:
    1. مطابقة الكلمات المفتاحية الدقيقة
    2. مطابقة المواضيع (topics) بوزن أعلى
    3. مطابقة الكلمات الفرعية
    """
    q_norm = _normalize(query)
    qwords = set(w for w in q_norm.split() if len(w) > 1)

    # إذا كان السؤال عن حكم شرعي، رجّح المصادر الفقهية
    is_fiqh_question = any(k in q_norm for k in ["حكم", "يجوز", "حرام", "حلال", "فرض", "سنه", "واجب", "مكروه", "مباح"])

    results = []
    for src in SEED_SOURCES:
        src_text_norm = _normalize(src["text"] + " " + src["reference"])
        src_words = set(src_text_norm.split())

        # 1) مطابقة الكلمات الدقيقة (وزن قوي)
        exact_matches = qwords & src_words
        exact_score = len(exact_matches) * 2.0

        # 2) مطابقة المواضيع (وزن أقوى)
        topic_matches = 0
        for topic in src.get("topics", []):
            t_norm = _normalize(topic)
            if t_norm in q_norm or any(t_norm in w or w in t_norm for w in qwords if len(w) > 2):
                topic_matches += 1
        topic_score = topic_matches * 3.0

        # 3) مطابقة الكلمات الفرعية (وزن متوسط)
        substring_matches = 0
        for q in qwords:
            if len(q) > 2 and q not in exact_matches:
                if q in src_text_norm:
                    substring_matches += 1
        substring_score = substring_matches * 1.0

        # 4) مكافأة للمصادر الفقهية عند السؤال عن حكم
        fiqh_bonus = 1.5 if (is_fiqh_question and src["source_type"] == "fiqh") else 0

        total_score = exact_score + topic_score + substring_score + fiqh_bonus

        if total_score > 0:
            results.append({**src, "_score": total_score})

    # الترتيب حسب النقاط
    results.sort(key=lambda x: x["_score"], reverse=True)

    # حساب similarity نسبي (للعرض فقط)
    if results:
        max_score = max(r["_score"] for r in results)
        for r in results:
            r["similarity"] = round(min(r["_score"] / max(max_score, 1), 1.0), 2)

    # حذف النقاط الداخلية قبل الإرجاع
    for r in results:
        r.pop("_score", None)

    return results[:top_k]


def source_count():
    return len(SEED_SOURCES)
