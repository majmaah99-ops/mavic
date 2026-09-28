import httpx
import json
from pathlib import Path

SOURCES_DIR = Path(__file__).parent.parent / "sources"

# --- 1. تحميل القرآن الكريم ---
def fetch_quran():
    print("📥 تحميل القرآن الكريم...")
    output_dir = SOURCES_DIR / "quran"
    output_dir.mkdir(parents=True, exist_ok=True)

    api_url = "https://api.al-salihin.com/data/quran-text/ar/surah"
    index_url = f"{api_url}/index.json"

    with httpx.Client(timeout=30) as client:
        try:
            print(f"  - جلب فهرس السور...")
            resp = client.get(index_url)
            resp.raise_for_status()
            surahs = resp.json()
            print(f"  ✅ {len(surahs)} سورة")

            total = 0
            for s in surahs:
                n = s["surah_number"]
                r = client.get(f"{api_url}/{n:03d}.json")
                r.raise_for_status()
                data = r.json()
                verses = []
                for v in data.get("verses", []):
                    verses.append({
                        "id": f"quran_{n}_{v['numberInSurah']}",
                        "text": v['text'],
                        "book": data['name_ar'],
                        "number": f"{n}:{v['numberInSurah']}",
                        "chapter": data['name_ar'],
                    })
                name = data['name_ar'].replace(' ', '_').replace('/', '-')
                out = output_dir / f"{n:03d}_{name}.json"
                out.write_text(json.dumps(verses, ensure_ascii=False, indent=2), encoding='utf-8')
                total += len(verses)
                print(f"  ✅ السورة {n}: {data['name_ar']} — {len(verses)} آية")
            print(f"🎉 القرآن: {total} آية")
        except Exception as e:
            print(f"❌ خطأ: {e}")

# --- 2. تحميل الأحاديث ---
def fetch_hadith():
    print("\n📥 تحميل الأحاديث...")
    tag = "v1.2.0"
    base = f"https://raw.githubusercontent.com/AhmedBaset/hadith-json/{tag}/db/by_book/the_9_books"
    books = {"bukhari": "صحيح البخاري", "muslim": "صحيح مسلم"}

    with httpx.Client(timeout=120) as client:
        for slug, name in books.items():
            print(f"  - تحميل {name}...")
            try:
                r = client.get(f"{base}/{slug}.json")
                r.raise_for_status()
                data = r.json()

                # إذا كانت البيانات قاموسًا، حوّلها إلى قائمة
                if isinstance(data, dict):
                    if 'hadiths' in data:
                        data = data['hadiths']
                    else:
                        data = list(data.values())

                if not isinstance(data, list):
                    print(f"  ⚠️ تخطي {name}: هيكل غير متوقع")
                    continue

                hadiths = []
                for h in data:
                    if not isinstance(h, dict): continue
                    if 'id' not in h or 'arabic' not in h: continue
                    hadiths.append({
                        "id": f"{slug}_{h['id']}",
                        "text": h['arabic'],
                        "book": name,
                        "number": str(h['id']),
                        "chapter": str(h.get('chapterId', '')),
                    })

                output_dir = SOURCES_DIR / "hadith"
                output_dir.mkdir(parents=True, exist_ok=True)
                (output_dir / f"{slug}.json").write_text(
                    json.dumps(hadiths, ensure_ascii=False, indent=2), encoding='utf-8'
                )
                print(f"  ✅ {name}: {len(hadiths)} حديث")
            except Exception as e:
                print(f"  ❌ فشل {name}: {e}")

if __name__ == "__main__":
    print("🚀 بدء تحميل المصادر...\n")
    fetch_quran()
    fetch_hadith()
    print("\n🎉 اكتمل تحميل جميع المصادر.")
