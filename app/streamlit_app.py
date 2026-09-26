import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.main import ask
from src.security import audit_log
from src.rag import source_count

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
    st.divider()
    st.metric("📚 عدد المصادر", source_count())
    st.metric("📝 سجل التدقيق", audit_log.count())

    if st.button("🔍 التحقق من سلسلة التدقيق"):
        if audit_log.verify_chain():
            st.success("✅ السلسلة سليمة")
        else:
            st.error("❌ السلسلة مكسورة")

st.subheader("❓ اطرح سؤالك أو الصق اقتباساً للتحقق منه")

st.markdown("**أمثلة سريعة:**")
cols = st.columns(3)
examples = [
    "ما حكم صلاة الوتر؟",
    "اذكر حديث إنما الأعمال بالنيات",
    "ما نصاب زكاة الذهب؟",
]
for col, ex in zip(cols, examples):
    with col:
        if st.button(ex, use_container_width=True):
            st.session_state.query = ex

query = st.text_input(
    "سؤالك:",
    value=st.session_state.get("query", ""),
    placeholder="اكتب سؤالك هنا...",
)

if st.button("🔍 تحقق", type="primary") and query:
    with st.spinner("جارٍ التحقق..."):
        result = ask(query)

    if "error" in result:
        st.error(f"❌ {result['error']}")
    else:
        if result.get("verification"):
            v = result["verification"]
            status_map = {
                "verified": ("✅ موثّق", "success"),
                "checkable": ("⚠️ قابل للتحقق", "warning"),
                "needs_review": ("⏸️ يتطلب مراجعة", "info"),
                "rejected": ("❌ مرفوض", "error"),
            }
            label, kind = status_map.get(v["status"], ("غير معروف", "info"))
            getattr(st, kind)(f"{label} — الثقة: {v['confidence']*100:.0f}% | {v['reason']}")

        if result.get("answer"):
            st.markdown("### 📖 الإجابة")
            st.info(result["answer"])
        elif result.get("referral"):
            st.markdown("### ⚠️ إحالة")
            st.warning(result["referral"])

        if result.get("sources"):
            st.markdown("### 📚 المصادر")
            for i, s in enumerate(result["sources"], 1):
                with st.expander(f"📖 المصدر {i}: {s['reference']}"):
                    st.write(s["text"])
                    if s.get("authenticity"):
                        st.caption(f"درجة الصحة: {s['authenticity']}")
                    st.caption(f"SHA-256: `{s['hash'][:32]}...`")
        else:
            st.warning("⚠️ لم يتم العثور على مصادر")

        st.caption(f"⏱️ زمن المعالجة: {result['processing_time_ms']:.1f}ms")

st.divider()
st.caption("© 2026 MAVIC — تحدي الذكاء الاصطناعي في خدمة المحتوى الإسلامي")
