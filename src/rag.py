"""قاعدة المصادر والبحث الدلالي الذكي"""
import re


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
        "source_id": "bukhari_1",
        "text": "إنما الأعمال بالنيات، وإنما لكل امرئ ما نوى",
        "reference": "صحيح البخاري، حديث رقم 1",
        "source_type": "hadith",
        "authenticity": "صحيح",
        "topics": ["نية", "أعمال", "إخلاص"],
    },
    {
        "source_id": "bukhari_8",
        "text": "بني الإسلام على خمس: شهادة أن لا إله إلا الله وأن محمداً رسول الله، وإقام الصلاة، وإيتاء الزكاة، وحج البيت، وصوم رمضان",
        "reference": "صحيح البخاري، حديث رقم 8",
        "source_type": "hadith",
        "authenticity": "صحيح",
        "topics": ["أركان الإسلام", "شهادة", "صلاة", "زكاة", "حج", "صوم"],
    },
    {
        "source_id": "muslim_2553",
        "text": "البر حسن الخلق، والإثم ما حاك في نفسك وكرهت أن يطلع عليه الناس",
        "reference": "صحيح مسلم، حديث رقم 2553",
        "source_type": "hadith",
        "authenticity": "صحيح",
        "topics": ["بر", "خلق", "إثم"],
    },
    {
        "source_id": "fiqh_zakat",
        "text": "نصاب الذهب عشرون مثقالاً، ومقدار زكاة النقود ربع العشر (2.5%) إذا بلغت النصاب وحال عليها الحول",
        "reference": "موسوعة الفقه الإسلامي، باب الزكاة",
        "source_type": "fiqh",
        "authenticity": "معتمد",
        "topics": ["زكاة", "نصاب", "ذهب", "نقود", "حكم"],
    },
    {
        "source_id": "fiqh_witr",
        "text": "صلاة الوتر سنة مؤكدة، ووقتها بعد صلاة العشاء إلى طلوع الفجر، وأقلها ركعة واحدة، وأكثرها إحدى عشرة ركعة",
        "reference": "موسوعة الفقه الإسلامي، باب الصلاة",
        "source_type": "fiqh",
        "authenticity": "معتمد",
        "topics": ["صلاة", "وتر", "حكم", "سنة", "قيام الليل"],
    },
    {
        "source_id": "fiqh_salah",
        "text": "الصلوات الخمس المفروضة: الفجر، الظهر، العصر، المغرب، العشاء. وهي فرض عين على كل مسلم بالغ عاقل",
        "reference": "موسوعة الفقه الإسلامي، باب الصلاة",
        "source_type": "fiqh",
        "authenticity": "معتمد",
        "topics": ["صلاة", "فريضة", "فرض", "حكم", "صلوات"],
    },
    {
        "source_id": "fiqh_sawm",
        "text": "صوم رمضان فرض عين على كل مسلم بالغ عاقل قادر، ووقته من طلوع الفجر إلى غروب الشمس",
        "reference": "موسوعة الفقه الإسلامي، باب الصيام",
        "source_type": "fiqh",
        "authenticity": "معتمد",
        "topics": ["صوم", "رمضان", "فريضة", "حكم"],
    },
    {
        "source_id": "fiqh_hajj",
        "text": "الحج فرض مرة واحدة في العمر على المستطيع، وأركانه: الإحرام، والطواف، والسعي، والوقوف بعرفة",
        "reference": "موسوعة الفقه الإسلامي، باب الحج",
        "source_type": "fiqh",
        "authenticity": "معتمد",
        "topics": ["حج", "فريضة", "أركان", "حكم"],
    },
]


def _normalize(text):
    text = re.sub(r"[^\w\s\u0600-\u06FF]", " ", text)
    return text.lower()


def search_sources(query, top_k=5):
    """
    بحث محسّن يعتمد على:
    1. مطابقة الكلمات المفتاحية
    2. مطابقة المواضيع (topics)
    3. ترجيح المصادر الفقهية عند السؤال عن "حكم"
    """
    qwords = set(_normalize(query).split())
    q_norm = _normalize(query)

    # إذا كان السؤال عن حكم/فقه، رجّح المصادر الفقهية
    is_fiqh_question = any(k in q_norm for k in ["حكم", "يجوز", "حرام", "حلال", "فرض", "سنة", "واجب", "مكروه", "مباح"])

    results = []
    for src in SEED_SOURCES:
        # مطابقة النص والمرجع
        sword = set(_normalize(src["text"] + " " + src["reference"]).split())
        common = qwords & sword
        if not common:
            for q in qwords:
                if len(q) > 2 and any(q in s for s in sword):
                    common.add(q)

        # مطابقة المواضيع (bonus)
        topic_hits = 0
        for topic in src.get("topics", []):
            if _normalize(topic) in q_norm:
                topic_hits += 1

        if common or topic_hits > 0:
            # حساب النقاط
            text_score = len(common) / max(len(qwords), 1)
            topic_score = topic_hits * 0.5
            total_score = text_score + topic_score

            # ترجيح المصادر الفقهية عند السؤال عن حكم
            if is_fiqh_question and src["source_type"] == "fiqh":
                total_score += 0.6

            results.append({**src, "similarity": min(total_score + 0.15, 0.99)})

    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results[:top_k]


def source_count():
    return len(SEED_SOURCES)
