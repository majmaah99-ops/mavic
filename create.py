import os

# المجلدات
for f in ["src/security","src/agents","src/rag","src/models","src/utils","app","data/sources/quran","data/sources/hadith","data/sources/fiqh","tests","docs","notebooks"]:
    os.makedirs(f, exist_ok=True)

# ملفات __init__
for f in ["src/__init__.py","src/security/__init__.py","src/agents/__init__.py","src/rag/__init__.py","src/models/__init__.py","src/utils/__init__.py","tests/__init__.py"]:
    open(f, "a").close()

# requirements
open("requirements.txt","w",encoding="utf-8").write("streamlit==1.31.0\npython-dotenv==1.0.1\npydantic==2.6.1\nloguru==0.7.2\nrequests==2.31.0\nnumpy==1.26.4\npandas==2.2.0\n")

# .gitignore
open(".gitignore","w",encoding="utf-8").write("__pycache__/\n*.py[cod]\nvenv/\n.env\ndata/audit_log.jsonl\n")

# README
open("README.md","w",encoding="utf-8").write("# MAVIC\n\nمنصة تحقق ذكية متعددة الوكلاء للمحتوى الإسلامي\n")

# streamlit_app
app_code = '''import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

st.set_page_config(page_title="MAVIC", page_icon="🛡️", layout="wide")
st.title("🛡️ MAVIC")
st.caption("منصة تحقق ذكية متعددة الوكلاء للمحتوى الإسلامي")

st.sidebar.header("ℹ️ عن المشروع")
st.sidebar.metric("📚 المصادر", 5)
st.sidebar.metric("📝 سجل التدقيق", 0)

query = st.text_input("❓ اطرح سؤالك:")
if st.button("🔍 تحقق", type="primary") and query:
    st.success(f"تم استلام سؤالك: {query}")
    st.info("نظام التحقق سيعمل قريباً")
'''
open("app/streamlit_app.py","w",encoding="utf-8").write(app_code)

print("=" * 50)
print("✅ تم إنشاء جميع الملفات!")
print("=" * 50)
for root, dirs, files in os.walk("."):
    level = root.count(os.sep)
    if "venv" in root or "__pycache__" in root: continue
    indent = "  " * level
    print(f"{indent}📁 {os.path.basename(root)}/")
    for file in files:
        print(f"{indent}  📄 {file}")