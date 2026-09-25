import os

# إنشاء المجلدات
folders = [
    "src/security", "src/agents", "src/rag", "src/models", "src/utils",
    "app", "data/sources/quran", "data/sources/hadith", "data/sources/fiqh",
    "tests", "docs", "notebooks"
]
for f in folders:
    os.makedirs(f, exist_ok=True)

# إنشاء ملفات __init__.py
init_files = ["src/__init__.py", "src/security/__init__.py", "src/agents/__init__.py",
              "src/rag/__init__.py", "src/models/__init__.py", "src/utils/__init__.py", "tests/__init__.py"]
for f in init_files:
    open(f, 'a').close()

# محتوى الملفات
files_content = {
    ".gitignore": "__pycache__/\n*.py[cod]\nvenv/\n.venv/\n.env\n.env.local\ndata/chroma_db/\ndata/audit_log.jsonl\n.vscode/\n.idea/\n.DS_Store\n*.bin\n*.safetensors\n.cache/\n",
    "requirements.txt": "streamlit==1.31.0\nfastapi==0.109.0\nuvicorn==0.27.0\npython-dotenv==1.0.1\npydantic==2.6.1\nlangchain==0.1.9\nlangchain-community==0.0.24\nchromadb==0.4.22\nsentence-transformers==2.5.1\ntransformers==4.38.0\nopenai==1.13.0\nllm-guard==0.3.7\ncryptography==42.0.5\npandas==2.2.0\nnumpy==1.26.4\nrequests==2.31.0\nloguru==0.7.2\npytest==8.0.0\n",
    ".env.example": "OPENAI_API_KEY=sk-your-key-here\nQURAN_API_KEY=your-quran-api-key\nCHROMA_DB_PATH=./data/chroma_db\nCOLLECTION_NAME=islamic_sources\nAUDIT_LOG_PATH=./data/audit_log.jsonl\nSOURCE_HASH_SALT=change-this-in-production\nMAX_QUERY_LENGTH=500\nRATE_LIMIT_PER_MINUTE=20\nAPP_ENV=development\nLOG_LEVEL=INFO\n",
    "README.md": "# 🛡️ MAVIC — Multi-Agent Verification for Islamic Content\n\nمنصة تحقق ذكية متعددة الوكلاء للمحتوى الإسلامي\n\n## 🎯 عن المشروع\nنظام متعدد الوكلاء يتحقق من المحتوى الإسلامي قبل عرضه، عبر 4 طبقات:\n1. Retriever Agent\n2. Verification Agent\n3. Fiqh Agent\n4. Referral Agent\n\n## 🚀 التشغيل\npip install -r requirements.txt\nstreamlit run app/streamlit_app.py\n\n## 📜 الترخيص\nMIT License\n",
    "Dockerfile": "FROM python:3.11-slim\n\nWORKDIR /app\n\nRUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*\n\nCOPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\n\nCOPY . .\n\nRUN useradd -m appuser && chown -R appuser:appuser /app\nUSER appuser\n\nEXPOSE 8501\n\nHEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1\n\nCMD streamlit run app/streamlit_app.py --server.port=8501 --server.address=0.0.0.0\n",
    "docker-compose.yml": "version: \"3.9\"\nservices:\n  mavic:\n    build: .\n    ports:\n      - \"8501:8501\"\n    env_file:\n      - .env\n    volumes:\n      - ./data:/app/data\n    restart: unless-stopped\n"
}

for filename, content in files_content.items():
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

print("✅ تم إنشاء جميع الملفات بنجاح!")