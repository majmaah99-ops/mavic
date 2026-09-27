"""MAVIC API + Static serving"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from pathlib import Path
import json

from agents import (
    check_injection, run_query, add_source, add_single_source,
    list_sources, delete_source, reindex_all, count_all, read_audit,
)

ROOT = Path(__file__).parent
STATIC = ROOT / "static"

app = FastAPI(title="MAVIC", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# -------- Models --------
class QueryModel(BaseModel):
    text: str

class SourceModel(BaseModel):
    category: str
    title: str
    text: str
    reference: str = ""
    trust: str = "صحيح"

# -------- API: Verify --------
@app.post("/api/verify")
def verify_endpoint(q: QueryModel):
    ok, msg = check_injection(q.text)
    if not ok: raise HTTPException(400, msg)
    return run_query(q.text)

# -------- API: Admin --------
@app.get("/api/admin/stats")
def stats():
    total, breakdown = count_all()
    return {"total": total, "breakdown": breakdown}

@app.get("/api/admin/sources")
def admin_list(category: str = None, q: str = None, limit: int = 100):
    items = list_sources(category)
    if q:
        q_low = q.lower()
        items = [i for i in items if q_low in str(i.get("title","")).lower() or q_low in str(i.get("text","")).lower()]
    return {"total": len(items), "items": items[:limit]}

@app.post("/api/admin/add")
def admin_add(s: SourceModel):
    """إضافة مصدر واحد من النموذج"""
    if not s.title.strip() or not s.text.strip():
        raise HTTPException(400, "العنوان والنص مطلوبان")
    result = add_single_source(s.category, s.title, s.text, s.reference, s.trust)
    # فهرس فوري
    _, _ = reindex_all()
    return {"status": "ok", "message": "✅ تمت الإضافة والفهرسة", "sha": result["sha"][:16]}

@app.post("/api/admin/upload")
async def admin_upload(
    category: str = Form(...),
    name: str = Form(...),
    file: UploadFile = File(...),
):
    if not file.filename.endswith(".json"):
        raise HTTPException(400, "يجب أن يكون ملف JSON")
    data = json.loads((await file.read()).decode("utf-8"))
    if not isinstance(data, list):
        raise HTTPException(400, "الملف يجب أن يكون قائمة JSON")
    result = add_source(category, name, data)
    _, _ = reindex_all()
    return {"status": "ok", "message": f"✅ أُضيف {result['count']} عنصر", "sha": result["sha"][:16]}

@app.delete("/api/admin/sources/{source_id}")
def admin_delete(source_id: str):
    if not delete_source(source_id):
        raise HTTPException(404, "لم يوجد")
    _, _ = reindex_all()
    return {"status": "ok", "message": "تم الحذف"}

@app.post("/api/admin/reindex")
def admin_reindex():
    n, stats = reindex_all()
    return {"status": "ok", "indexed": n, "breakdown": stats}

@app.get("/api/admin/audit")
def admin_audit(limit: int = 30):
    return {"items": read_audit(limit)}

@app.get("/health")
def health():
    total, _ = count_all()
    return {"status": "ok", "sources": total}

# -------- Static pages --------
@app.get("/", response_class=HTMLResponse)
def root():
    return FileResponse(STATIC / "index.html")

@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    return FileResponse(STATIC / "admin.html")

# Mount static (CSS/JS إذا احتجنا لاحقًا)
app.mount("/static", StaticFiles(directory=STATIC), name="static")

@app.on_event("startup")
def startup():
    print("🚀 MAVIC starting...")
    total, stats = count_all()
    print(f"📚 مصادر: {total} - {stats}")
