import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

st.set_page_config(page_title="MAVIC", page_icon="🛡️", layout="wide")
st.title("🛡️ MAVIC")
st.caption("منصة تحقق ذكية متعددة الوكلاء للمحتوى الإسلامي")

with st.sidebar:
    st.header("ℹ️ عن المشروع")
    st.markdown("""
    **المسار:** أدوات المعرفة والتحقق
    **الوكلاء:**
    - 🔍 Retriever
    - ✅ Verification
    - ⚖️ Fiqh
    - 📞 Referral
    """)
    st.metric("📚 عدد المصادر", 5)
    st.metric("📝 سجل التدقيق", 0)

st.subheader("❓ اطرح سؤالك أو الصق اقتباساً للتحقق منه")

cols = st.columns(3)
examples = ["ما حكم صلاة الوتر؟", "اذكر حديث إنما الأعمال بالنيات", "ما نصاب زكاة الذهب؟"]
for col, ex in zip(cols, examples):
    with col:
        if st.button(ex, use_container_width=True):
            st.session_state.query = ex

query = st.text_input("سؤالك:", value=st.session_state.get("query", ""), placeholder="اكتب سؤالك هنا...")

if st.button("🔍 تحقق", type="primary") and query:
    st.success(f"✅ تم استلام سؤالك: {query}")
    st.info("🔄 النظام يعمل حالياً في وضع مبسط. الإجابة الكاملة ستظهر بعد تفعيل الوكلاء.")

st.divider()
st.caption("© 2026 MAVIC — تحدي الذكاء الاصطناعي في خدمة المحتوى الإسلامي")
