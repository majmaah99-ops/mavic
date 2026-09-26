"""قاعدة المصادر الشاملة — موسوعة فقهية + أحاديث + قرآن"""
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
    "اذكر", "أعطني", "قل", "أخبرني", "حدثني", "وضح", "اشرح", "بين",
}


# ========== الموسوعة الفقهية الشاملة ==========
SEED_SOURCES = [
    # ============ الطهارة ============
    {
        "source_id": "fiqh_wudu",
        "text": "الوضوء واجب للصلاة والطواف ومس المصحف. فرائضه: النية، غسل الوجه، غسل اليدين إلى المرفقين، مسح الرأس، غسل الرجلين إلى الكعبين، الترتيب، الموالاة.",
        "reference": "موسوعة الفقه الإسلامي، باب الطهارة",
        "source_type": "fiqh",
        "authenticity": "معتمد",
        "topics": ["وضوء", "طهارة", "صلاة", "فرائض"],
    },
    {
        "source_id": "fiqh_tayammum",
        "text": "التيمم بديل عن الوضوء والغسل عند عدم الماء أو العجز عن استعماله. يُضرب باليدين على الصعيد الطاهر ثم يُمسح بهما الوجه والكفان.",
        "reference": "موسوعة الفقه الإسلامي، باب التيمم",
        "source_type": "fiqh",
        "authenticity": "معتمد",
        "topics": ["تيمم", "طهارة", "ماء"],
    },
    
    # ============ الصلاة ============
    {
        "source_id": "fiqh_salah_5",
        "text": "الصلوات الخمس المفروضة: الفجر (ركعتان)، الظهر (أربع)، العصر (أربع)، المغرب (ثلاث)، العشاء (أربع). وهي فرض عين على كل مسلم بالغ عاقل.",
        "reference": "موسوعة الفقه الإسلامي، باب الصلاة",
        "source_type": "fiqh",
        "authenticity": "معتمد",
        "topics": ["صلاة", "فرض", "صلوات خمس", "فجر", "ظهر", "عصر", "مغرب", "عشاء"],
    },
    {
        "source_id": "fiqh_travel_prayer",
        "text": "صلاة المسافر: يُباح له قصر الصلاة الرباعية إلى ركعتين إذا سافر مسافة قصر (حوالي 80 كم) وكان سفره مباحاً. ويُباح له الجمع بين الظهر والعصر، وبين المغرب والعشاء، جمع تقديم أو تأخير.",
        "reference": "موسوعة الفقه الإسلامي، باب صلاة المسافر",
        "source_type": "fiqh",
        "authenticity": "معتمد",
        "topics": ["قصر", "جمع", "مسافر", "صلاة المسافر", "سفر", "ركعتين", "جمع تقديم", "جمع تأخير"],
    },
    {
        "source_id": "fiqh_witr",
        "text": "صلاة الوتر سنة مؤكدة، ووقتها بعد صلاة العشاء إلى طلوع الفجر، وأقلها ركعة واحدة، وأكثرها إحدى عشرة ركعة.",
        "reference": "موسوعة الفقه الإسلامي، باب صلاة التطوع",
        "source_type": "fiqh",
        "authenticity": "معتمد",
        "topics": ["صلاة", "وتر", "سنة", "قيام الليل", "تطوع"],
    },
    {
        "source_id": "fiqh_jumuah",
        "text": "صلاة الجمعة فرض عين على الذكور الأحرار البالغين المقيمين القادرين. وقتها وقت صلاة الظهر، وتتكون من خطبتين وركعتين.",
        "reference": "موسوعة الفقه الإسلامي، باب الجمعة",
        "source_type": "fiqh",
        "authenticity": "معتمد",
        "topics": ["جمعة", "صلاة الجمعة", "خطبة", "فرض"],
    },
    {
        "source_id": "fiqh_sick_prayer",
        "text": "صلاة المريض: يصلي قائماً، فإن لم يستطع فقاعداً، فإن لم يستطع فعلى جنب، فإن لم يستطع فيصلي مستلقياً بالإيماء. ولا تسقط الصلاة عن المسلم في أي حال.",
        "reference": "موسوعة الفقه الإسلامي، باب صلاة المريض",
        "source_type": "fiqh",
        "authenticity": "معتمد",
        "topics": ["مريض", "صلاة المريض", "قاعداً", "مستلقياً"],
    },
    
    # ============ الزكاة ============
    {
        "source_id": "fiqh_zakat_gold",
        "text": "نصاب الذهب عشرون مثقالاً (حوالي 85 جرام)، ونصاب الفضة مئتا درهم (حوالي 595 جرام). ومقدار زكاة النقود ربع العشر (2.5%) إذا بلغت النصاب وحال عليها الحول.",
        "reference": "موسوعة الفقه الإسلامي، باب الزكاة",
        "source_type": "fiqh",
        "authenticity": "معتمد",
        "topics": ["زكاة", "نصاب", "ذهب", "فضة", "نقود", "حول"],
    },
    {
        "source_id": "fiqh_zakat_jewelry",
        "text": "زكاة الحلي (الذهب الملبوس): اختلف الفقهاء على قولين: الجمهور (المالكية والشافعية والحنابلة) يرون أن حلي المرأة المباح للزينة لا تجب فيه الزكاة إذا كان في حدود المعتاد، ما لم يكن كنزاً أو ادخاراً. والحنفية يرون وجوب الزكاة في الحلي إذا بلغ النصاب. والراجح قول الجمهور إذا كان للزينة المعتادة.",
        "reference": "موسوعة الفقه الإسلامي، باب زكاة الحلي",
        "source_type": "fiqh",
        "authenticity": "معتمد",
        "topics": ["زكاة", "حلي", "ذهب ملبوس", "ذهب مستعمل", "زينة", "نصاب", "حكم"],
    },
    {
        "source_id": "fiqh_zakat_used_gold",
        "text": "الذهب المستعمل: إذا كان للزينة المعتادة فلا زكاة فيه عند الجمهور. وإذا كان للتجارة أو الادخار أو الكنز فتجب فيه الزكاة إذا بلغ النصاب (20 مثقالاً = 85 جرام) وحال عليه الحول.",
        "reference": "موسوعة الفقه الإسلامي، باب زكاة الذهب المستعمل",
        "source_type": "fiqh",
        "authenticity": "معتمد",
        "topics": ["زكاة", "ذهب مستعمل", "ذهب ملبوس", "تجارة", "ادخار", "كنز"],
    },
    {
        "source_id": "fiqh_zakah_types",
        "text": "أنواع الزكاة: زكاة المال (النقود والذهب والفضة)، زكاة الأنعام، زكاة الزروع والثمار، زكاة التجارة، زكاة الفطر. وزكاة المال تجب إذا بلغ النصاب وحال عليه الحول.",
        "reference": "موسوعة الفقه الإسلامي، باب الزكاة",
        "source_type": "fiqh",
        "authenticity": "معتمد",
        "topics": ["زكاة", "أنواع", "مال", "تجارة", "فطر", "أنعام", "زروع"],
    },
    {
        "source_id": "fiqh_zakat_animals",
        "text": "زكاة الأنعام: الإبل والبقر والغنم إذا بلغت النصاب وحال عليها الحول. ونصاب الإبل خمس، ونصاب البقر ثلاثون، ونصاب الغنم أربعون.",
        "reference": "موسوعة الفقه الإسلامي، باب زكاة الأنعام",
        "source_type": "fiqh",
        "authenticity": "معتمد",
        "topics": ["زكاة", "أنعام", "إبل", "بقر", "غنم", "نصاب"],
    },
    {
        "source_id": "fiqh_zakat_fitr",
        "text": "زكاة الفطر: صاع من طعام (حوالي 2.5 كجم) عن كل مسلم، تُخرج قبل صلاة عيد الفطر. وهي واجبة على من ملك ما زاد عن قوته وقوت عياله يوم العيد.",
        "reference": "موسوعة الفقه الإسلامي، باب زكاة الفطر",
        "source_type": "fiqh",
        "authenticity": "معتمد",
        "topics": ["زكاة الفطر", "صاع", "عيد", "فطر"],
    },
    
    # ============ الصيام ============
    {
        "source_id": "fiqh_sawm_ramadan",
        "text": "صوم رمضان فرض عين على كل مسلم بالغ عاقل قادر. ووقته من طلوع الفجر إلى غروب الشمس، ويجب فيه الإمساك عن الطعام والشراب والجماع.",
        "reference": "موسوعة الفقه الإسلامي، باب الصيام",
        "source_type": "fiqh",
        "authenticity": "معتمد",
        "topics": ["صوم", "رمضان", "صيام", "فرض", "إمساك"],
    },
    {
        "source_id": "fiqh_fasting_traveler",
        "text": "المسافر والمريض يجوز لهما الفطر في رمضان، وعليهما القضاء. قال تعالى: (فمن كان منكم مريضاً أو على سفر فعدة من أيام أخر).",
        "reference": "موسوعة الفقه الإسلامي، باب الصيام",
        "source_type": "fiqh",
        "authenticity": "معتمد",
        "topics": ["صيام", "مسافر", "مريض", "فطر", "قضاء", "رمضان"],
    },
    
    # ============ الحج ============
    {
        "source_id": "fiqh_hajj",
        "text": "الحج فرض مرة واحدة في العمر على المستطيع. وأركانه: الإحرام، والطواف، والسعي، والوقوف بعرفة. وواجباته: المبيت بمنى، والمبيت بمزدلفة، ورمي الجمار، والحلق، وطواف الوداع.",
        "reference": "موسوعة الفقه الإسلامي، باب الحج",
        "source_type": "fiqh",
        "authenticity": "معتمد",
        "topics": ["حج", "عمرة", "إحرام", "طواف", "سعي", "عرفة"],
    },
    
    # ============ الأسرة والميراث ============
    {
        "source_id": "fiqh_marriage",
        "text": "الزواج سنة مؤكدة لمن قدر عليه. وأركانه: الإيجاب والقبول، وولي المرأة، والشهود. ومن شروطه: تعيين الزوجين، ورضاهما، وعدم الموانع الشرعية.",
        "reference": "موسوعة الفقه الإسلامي، باب النكاح",
        "source_type": "fiqh",
        "authenticity": "معتمد",
        "topics": ["زواج", "نكاح", "إيجاب", "قبول", "ولي", "شهود"],
    },
    {
        "source_id": "fiqh_inheritance",
        "text": "أصحاب الفروض في الميراث: الزوج، الزوجة، الأب، الأم، الجد، الجدة، الابن، البنت، الأخ، الأخت. ويُقسم الإرث بعد سداد الديون وتنفيذ الوصية (في حدود الثلث).",
        "reference": "موسوعة الفقه الإسلامي، باب الميراث",
        "source_type": "fiqh",
        "authenticity": "معتمد",
        "topics": ["ميراث", "تركة", "ورثة", "فرض", "وصية", "ديون"],
    },
    
    # ============ الأخلاق ============
    {
        "source_id": "fiqh_akhlaq",
        "text": "من أهم الأخلاق الإسلامية: الصدق، الأمانة، البر، الإحسان، العدل، الرحمة، التواضع، الحلم، العفة. قال تعالى: (وإنك لعلى خلق عظيم).",
        "reference": "موسوعة الفقه الإسلامي، باب الأخلاق",
        "source_type": "fiqh",
        "authenticity": "معتمد",
        "topics": ["أخلاق", "صدق", "أمانة", "بر", "إحسان", "عدل", "رحمة"],
    },
    
    # ============ قرآن ============
    {
        "source_id": "quran_2_255",
        "text": "اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ ۚ لَا تَأْخُذُهُ سِنَةٌ وَلَا نَوْمٌ ۚ لَهُ مَا فِي السَّمَاوَاتِ وَمَا فِي الْأَرْضِ",
        "reference": "سورة البقرة، الآية 255 (آية الكرسي)",
        "source_type": "quran",
        "authenticity": "قطعي الثبوت",
        "topics": ["الله", "توحيد", "قرآن", "آية الكرسي", "عقيدة"],
    },
    {
        "source_id": "quran_103_1",
        "text": "وَالْعَصْرِ إِنَّ الْإِنْسَانَ لَفِي خُسْرٍ إِلَّا الَّذِينَ آمَنُوا وَعَمِلُوا الصَّالِحَاتِ وَتَوَاصَوْا بِالْحَقِّ وَتَوَاصَوْا بِالصَّبْرِ",
        "reference": "سورة العصر",
        "source_type": "quran",
        "authenticity": "قطعي الثبوت",
        "topics": ["صبر", "إيمان", "عمل صالح", "حق"],
    },
    {
        "source_id": "quran_2_286",
        "text": "لَا يُكَلِّفُ اللَّهُ نَفْسًا إِلَّا وُسْعَهَا ۚ لَهَا مَا كَسَبَتْ وَعَلَيْهَا مَا اكْتَسَبَتْ",
        "reference": "سورة البقرة، الآية 286",
        "source_type": "quran",
        "authenticity": "قطعي الثبوت",
        "topics": ["تيسير", "تكليف", "تخفيف", "رخصة"],
    },
]


# ========== دوال المعالجة ==========

def _normalize(text):
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
    text = re.sub(r"[^\w\s\u0600-\u06FF]", " ", text)
    text = re.sub(r"[إأآا]", "ا", text)
    text = re.sub(r"[ىي]", "ي", text)
    text = re.sub(r"ة", "ه", text)
    return text.lower().strip()


def _keywords_normalized(text):
    words = _normalize(text).split()
    return set(w for w in words if len(w) > 2 and w not in STOP_WORDS)


def _keywords_original(text):
    clean = re.sub(r"[\u064B-\u065F\u0670]", "", text)
    clean = re.sub(r"[^\w\s\u0600-\u06FF]", " ", clean)
    words = clean.split()
    return [w for w in words if len(w) > 2 and w not in STOP_WORDS]


# ========== البحث في المصادر المحلية ==========

def search_local_sources(query, top_k=5):
    """البحث مع ترجيح قوي للمواضيع (Topics)"""
    q_keywords = _keywords_normalized(query)
    q_norm = _normalize(query)

    if not q_keywords:
        return []

    is_fiqh_question = any(k in q_norm for k in [
        "حكم", "يجوز", "حرام", "حلال", "فرض", "سنه", "واجب",
        "مكروه", "مباح", "قصر", "جمع", "زكاه", "صيام", "حج", "صلاه"
    ])

    results = []
    for src in SEED_SOURCES:
        src_keywords = _keywords_normalized(src["text"] + " " + src["reference"])
        exact_matches = q_keywords & src_keywords
        exact_score = len(exact_matches) * 3.0

        # ترجيح قوي للمواضيع
        topic_matches = 0
        for topic in src.get("topics", []):
            t_norm = _normalize(topic)
            for qk in q_keywords:
                if t_norm == qk or t_norm in qk or qk in t_norm:
                    topic_matches += 1
                    break

        topic_weight = 5.0 if is_fiqh_question else 3.0
        topic_score = topic_matches * topic_weight

        fiqh_bonus = 1.5 if (is_fiqh_question and src["source_type"] == "fiqh") else 0

        total_score = exact_score + topic_score + fiqh_bonus
        if total_score >= 3.0:
            results.append({**src, "_score": total_score})

    results.sort(key=lambda x: x["_score"], reverse=True)
    return [{k: v for k, v in r.items() if k != "_score"} for r in results[:top_k]]


# ========== البحث في قاعدة بيانات الأحاديث ==========

def search_hadith_db(query, top_k=5):
    if not DB_PATH.exists():
        return []

    kws_original = _keywords_original(query)
    kws_normalized = list(_keywords_normalized(query))

    all_keywords = []
    seen_kw = set()
    for kw in kws_original + kws_normalized:
        if kw not in seen_kw and len(kw) > 2:
            seen_kw.add(kw)
            all_keywords.append(kw)

    if not all_keywords:
        return []

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


# ========== الدالة الموحدة ==========

def search_sources_enhanced(query, top_k=5):
    local_results = search_local_sources(query, top_k=5)
    hadith_results = search_hadith_db(query, top_k=5)

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
