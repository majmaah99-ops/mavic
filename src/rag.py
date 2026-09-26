"""قاعدة المصادر والبحث الدلالي الذكي"""
import re
import requests

# ... (الكود الحالي للمصادر المحلية يبقى كما هو) ...

# === دوال جديدة لجلب البيانات من APIs ===

def fetch_quran_verse(surah, ayah):
    """
    جلب آية من القرآن الكريم باستخدام Quran.com API
    """
    url = f"https://api.quran.com/api/v4/verses/by_key/{surah}:{ayah}"
    params = {"language": "ar", "words": "true"}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        verse = data.get("verse", {})
        return {
            "source_id": f"quran_{surah}_{ayah}",
            "text": verse.get("text_uthmani", ""),
            "reference": f"سورة {verse.get('verse_key', '')}",
            "source_type": "quran",
            "authenticity": "قطعي الثبوت",
        }
    except Exception as e:
        print(f"Error fetching Quran verse: {e}")
        return None


def fetch_hadith(book, hadith_number):
    """
    جلب حديث من Hadith API (مثال: صحيح البخاري)
    """
    url = f"https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/ara-{book}/{hadith_number}.json"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        hadith = data.get("hadiths", [{}])[0]
        return {
            "source_id": f"hadith_{book}_{hadith_number}",
            "text": hadith.get("text", ""),
            "reference": f"صحيح {book.capitalize()}، حديث رقم {hadith_number}",
            "source_type": "hadith",
            "authenticity": "صحيح",
        }
    except Exception as e:
        print(f"Error fetching Hadith: {e}")
        return None


def search_sources_enhanced(query, top_k=5):
    """
    بحث محسّن يجمع بين المصادر المحلية والـ APIs
    """
    # 1. البحث في المصادر المحلية (المنطق الحالي)
    local_results = search_sources(query, top_k=top_k)

    # 2. البحث في الـ APIs (مثال: إذا كان السؤال يذكر سورة محددة)
    api_results = []
    surah_match = re.search(r"سورة\s+(\w+)\s+(\d+)", query)
    if surah_match:
        surah = surah_match.group(1)
        ayah = surah_match.group(2)
        # يمكنك هنا ربط اسم السورة برقمها، أو استخدام واجهة بحث أخرى
        # هذا مثال توضيحي، قد تحتاج لتعديله
        verse = fetch_quran_verse(surah, ayah)
        if verse:
            api_results.append(verse)

    # 3. دمج النتائج (مع إعطاء أولوية للمصادر المحلية)
    all_results = local_results + api_results
    return all_results[:top_k]
