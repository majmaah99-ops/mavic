# MAVIC - QAT Hub Deployment

## ملفات النشر
- requirements.txt: مكتبات خفيفة (بدون chromadb)
- runtime.txt: python-3.11.9
- packages.txt: فارغ
- app/streamlit_app.py: نقطة الدخول

## التشغيل المحلي (Windows PowerShell)
cd C:\Users\xp-55\Documents\GitHub\mavic
pip install -r requirements.txt
python build_db.py
python scripts/build_unified.py
streamlit run app/streamlit_app.py

## النشر على QAT Hub
1. git add .
2. git commit -m "fix: qat hub deploy - lightweight requirements"
3. git push origin main
4. في QAT Hub اضغط Redeploy
