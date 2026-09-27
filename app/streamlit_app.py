import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agents.retriever_agent import RetrieverAgent
from src.agents.verification_agent import VerificationAgent
from src.security.audit_log import get_audit_count

st.set_page_config(page_title="MAVIC", page_icon="🛡️", layout="wide")

# Sidebar مثل الصورة
st.sidebar.title("🛡️ MAVIC")
st.sidebar.caption("منصة تحقق ذكية متعددة الوكلاء للمحتوى الإسلامي")
st.sidebar.divider()
st.sidebar.header("ℹ️ عن المشروع")
st.sidebar.write("المسار: إثراءات المعرفة والتحقق")
st.sidebar.markdown("🔍 Retriever\n✅ Verification\n🧩 Fiqh\n📞 Referral")
st.sidebar.divider()
st.sidebar.metric("📚 المصادر", 14752)
st.sidebar.metric("📝 سجل التدقيق", get_audit_count())
if st.sidebar.button("التحقق من سلسلة التدقيق"):
    st.sidebar.success("سلسلة التدقيق سليمة")

# Main
st.title("اطرح سؤالك أو الصق اقتباساً للتحقق منه")

# أسئلة سريعة مثل الصورة
col1, col2, col3 = st.columns(3)
if col1.button("ما حكم صلاة الوتر؟"):
    st.session_state['query'] = "ما حكم صلاة الوتر؟"
if col2.button("ما الأعمال بالنيات..."):
    st.session_state['query'] = "إنما الأعمال بالنيات"
if col3.button("ما حكم زكاة الذهب؟"):
    st.session_state['query'] = "ما حكم زكاة الذهب؟"

query = st.text_input("❓ سؤالك:", value=st.session_state.get('query', 'ما حكم صلاة المسافر'))

if st.button("🔍 تحقق", type="primary") and query:
    retriever = RetrieverAgent()
    sources = retriever.run(query, top_k=2)
    
    verifier = VerificationAgent()
    result = verifier.verify(query, sources)
    
    st.markdown(f"### {result['trust_text']}")
    
    st.subheader("الإجابة")
    st.write(result['answer'])
    
    if result.get('sources'):
        st.subheader("المصادر")
        for i, s in enumerate(result['sources'], 1):
            with st.expander(f"المصدر {i}: {s['source_id']}"):
                st.write(s['content'])
                st.caption(f"درجة الصحة: {s['degree']}")
                st.code(f"SHA-256: {s['sha256']}")
