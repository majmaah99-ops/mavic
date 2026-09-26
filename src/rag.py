"""قاعدة المصادر والبحث الدلالي البسيط"""
import re


SEED_SOURCES = [
    {
        "source_id": "quran_2_255",
        "text": "اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ ۚ لَا تَأْخُذُهُ سِنَةٌ وَلَا نَوْمٌ",
        "reference": "سورة البقرة، الآية 255 (آية الكرسي)",
        "source_type": "quran",
        "authenticity": "قطعي الثبوت",
    },
    {
        "source_id": "quran_103_1",
        "text": "وَالْعَصْرِ إِنَّ الْإِنْسَانَ لَفِي خُسْرٍ إِلَّا الَّذِينَ آمَنُوا وَعَمِلُوا الصَّالِحَاتِ",
        "reference": "سورة العصر",
        "source_type": "quran",
        "authenticity": "قطعي الثبوت",
    },
    {
        "source_id": "bukhari_1",
        "text": "إنما الأعمال بالنيات، وإنما لكل امرئ ما نوى",
        "reference": "صحيح البخاري، حديث رقم 1",
        "source_type": "hadith",
        "authenticity": "صحيح",
    },
    {
        "source_id": "bukhari_8",
        "text": "بني الإسلام على خمس: شهادة أن لا إله إلا الله وأن محمداً رسول الله، وإقام الصلاة، وإيتاء الزكاة، وحج البيت، وصوم رمضان",
        "reference": "صحيح البخاري، حديث رقم 8",
        "source_type": "hadith",
        "authenticity": "صحيح",
    },
    {
        "source_id": "muslim_2553",
        "text": "البر حسن الخلق، والإثم ما حاك في نفسك وكرهت أن يطلع عليه الناس",
        "reference": "صحيح مسلم، حديث رقم 2553",
        "source_type": "hadith",
        "authenticity": "صحيح",
    },
    {
        "source_id": "fiqh_zakat",
        "text": "نصاب الذهب عشرون مثقالاً، ومقدار زكاة النقود ربع العشر (2.5%) إذا بلغت النصاب وحال عليها الحول",
        "reference": "موسوعة الفقه الإسلامي، باب الزكاة",
        "source_type": "fiqh",
        "authenticity": "معتمد",
    },
    {
        "source_id": "fiqh_witr",
        "text": "صلاة الوتر سنة مؤكدة، ووقتها بعد صلاة العشاء إلى طلوع الفجر، وأقلها ركعة واحدة",
        "reference": "موسوعة الفقه الإسلامي، باب الصلاة",
        "source_type": "fiqh",
        "authenticity": "معتمد",
    },
]


def _normalize(text):
    text = re.sub(r"[^\w\s\u0600-\u06FF]", " ", text)
    return text.lower()


def search_sources(query, top_k=5):
    qwords = set(_normalize(query).split())
    results = []
    for src in SEED_SOURCES:
        sword = set(_normalize(src["text"] + " " + src["reference"]).split())
        common = qwords & sword
        if not common:
            for q in qwords:
                if len(q) > 2 and any(q in s for s in sword):
                    common.add(q)
        if common:
            score = len(common) / max(len(qwords), 1)
            results.append({**src, "similarity": min(score + 0.2, 0.99)})
    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results[:top_k]


def source_count():
    return len(SEED_SOURCES)
