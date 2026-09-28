import httpx
import json
import time
import sys
from pathlib import Path

SOURCES_DIR = Path(__file__).parent.parent / "sources"
OUT = SOURCES_DIR / "quran"
OUT.mkdir(parents=True, exist_ok=True)

print("=" * 50)
print("🚀 بدء تحميل القرآن من api.quran.com")
print(f"📁 مجلد الحفظ: {OUT}")
print("=" * 50)

API = "https://api.quran.com/api/v4"

# اختبار الاتصال أولًا
print("\n[1/3] اختبار الاتصال بـ API...")
try:
    with httpx.Client(timeout=30) as c:
        r = c.get(f"{API}/chapters?language=ar")
        print(f"  → HTTP Status: {r.status_code}")
        r.raise_for_status()
        data = r.json()
        chapters = data.get("chapters", [])
        print(f"  ✅ تم الاتصال. عدد السور: {len(chapters)}")
except Exception as e:
    print(f"  ❌ فشل الاتصال: {e}")
    sys.exit(1)

if not chapters:
    print("❌ لا توجد سور في الاستجابة")
    sys.exit(1)

# التحميل
print("\n[2/3] تحميل الآيات...")
total = 0
failed = []

with httpx.Client(timeout=60) as c:
    for i, ch in enumerate(chapters, 1):
        n = ch["id"]
        name = ch["name_arabic"].replace(" ", "_").replace("/", "-")
        out_file = OUT / f"{n:03d}_{name}.json"
        
        if out_file.exists():
            try:
                count = len(json.load(open(out_file, encoding="utf-8")))
                total += count
                print(f"  ⏭️  [{i}/114] {n:3d}. {ch['name_arabic']} — موجود ({count})")
                continue
            except:
                pass
        
        try:
            r = c.get(
                f"{API}/quran/verses/uthmani",
                params={"chapter_number": n}
            )
            r.raise_for_status()
            verses = r.json().get("verses", [])
            
            items = [
                {
                    "id": f"quran_{v['verse_key'].replace(':', '_')}",
                    "text": v["text_uthmani"],
                    "book": ch["name_arabic"],
                    "number": v["verse_key"],
                    "chapter": ch["name_arabic"],
                }
                for v in verses
            ]
            
            out_file.write_text(
                json.dumps(items, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            total += len(items)
            print(f"  ✅ [{i}/114] {n:3d}. {ch['name_arabic']} — {len(items)} آية")
            time.sleep(0.1)
        except Exception as e:
            print(f"  ❌ [{i}/114] {n:3d}. {ch['name_arabic']} — فشل: {e}")
            failed.append(n)

# النتيجة
print("\n[3/3] النتيجة النهائية")
print("=" * 50)
print(f"✅ مجموع الآيات: {total}")
print(f"📁 عدد الملفات: {len(list(OUT.glob('*.json')))}")
if failed:
    print(f"⚠️  سور فشلت: {failed}")
else:
    print("🎉 اكتمل بدون أخطاء!")
print("=" * 50)
