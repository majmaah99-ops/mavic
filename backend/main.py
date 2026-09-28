"""MAVIC API - نسخة مصححة لـ Render"""
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel
from pathlib import Path
import json, traceback, os
from agents import check_injection, run_query, add_source, add_single_source, list_sources, delete_source, reindex_all, count_all, read_audit, _init_chroma

ROOT = Path(__file__).parent
STATIC = ROOT / "static"
docs_url = "/docs" if os.environ.get("RENDER") is None else None
app = FastAPI(title="MAVIC", version="2.0.1-fixed", docs_url=docs_url, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.exception_handler(Exception)
async def json_exception_handler(request: Request, exc: Exception):
    print(f"❌ Exception at {request.url.path}: {exc}")
    traceback.print_exc()
    return JSONResponse(status_code=500, content={"detail": f"خطأ داخلي: {type(exc).__name__}: {str(exc)[:500]}", "path": str(request.url.path)})

class QueryModel(BaseModel):
    text: str
class SourceModel(BaseModel):
    category: str; title: str; text: str; reference: str = ""; trust: str = "صحيح"

@app.post("/api/verify")
def verify_endpoint(q: QueryModel):
    ok, msg = check_injection(q.text)
    if not ok: raise HTTPException(400, msg)
    try: return run_query(q.text)
    except Exception as e: traceback.print_exc(); raise HTTPException(500, f"خطأ في التحقق: {str(e)[:200]}")

@app.get("/api/admin/stats")
def stats():
    total, breakdown = count_all()
    chroma_count = 0
    try:
        _init_chroma()
        from agents import _collection
        if _collection: chroma_count = _collection.count()
    except Exception as e: chroma_count = f"error: {e}"
    return {"total": total, "breakdown": breakdown, "chroma_count": chroma_count}

@app.get("/api/admin/sources")
def admin_list(category: str = None, q: str = None, limit: int = 100):
    items = list_sources(category)
    if q:
        q_low = q.lower()
        items = [i for i in items if q_low in str(i.get("title", "")).lower() or q_low in str(i.get("text", "")).lower()]
    return {"total": len(items), "items": items[:limit]}

@app.post("/api/admin/add")
def admin_add(s: SourceModel):
    if not s.title.strip() or not s.text.strip(): raise HTTPException(400, "العنوان والنص مطلوبان")
    result = add_single_source(s.category, s.title, s.text, s.reference, s.trust)
    reindex_all()
    return {"status": "ok", "message": "✅ تمت الإضافة والفهرسة", "sha": result["sha"][:16]}

@app.post("/api/admin/upload")
async def admin_upload(category: str = Form(...), name: str = Form(...), file: UploadFile = File(...)):
    if not file.filename.endswith(".json"): raise HTTPException(400, "يجب أن يكون ملف JSON")
    data = json.loads((await file.read()).decode("utf-8"))
    if not isinstance(data, list): raise HTTPException(400, "الملف يجب أن يكون قائمة JSON")
    result = add_source(category, name, data)
    reindex_all()
    return {"status": "ok", "message": f"✅ أُضيف {result['count']} عنصر", "sha": result["sha"][:16]}

@app.delete("/api/admin/sources/{source_id}")
def admin_delete(source_id: str):
    if not delete_source(source_id): raise HTTPException(404, "لم يوجد")
    reindex_all()
    return {"status": "ok", "message": "تم الحذف"}

@app.post("/api/admin/reindex")
def admin_reindex():
    try: n, st = reindex_all(); return {"status": "ok", "indexed": n, "breakdown": st}
    except Exception as e: traceback.print_exc(); raise HTTPException(500, f"فشل الفهرسة: {str(e)}")

@app.get("/api/admin/audit")
def admin_audit(limit: int = 30): return {"items": read_audit(limit)}

@app.get("/health")
def health():
    try:
        total, breakdown = count_all()
        chroma_count = 0
        try:
            _init_chroma()
            from agents import _collection
            if _collection: chroma_count = _collection.count()
        except Exception as e: chroma_count = f"error: {e}"
        return {"status": "ok", "sources": total, "breakdown": breakdown, "chroma": chroma_count}
    except Exception as e: return {"status": "error", "error": str(e)}

@app.get("/", response_class=HTMLResponse)
def root():
    index = STATIC / "index.html"
    if index.exists(): return FileResponse(index)
    return HTMLResponse("<h1>MAVIC API - اذهب إلى /admin</h1>")

@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    admin = STATIC / "admin.html"
    if admin.exists(): return FileResponse(admin)
    return HTMLResponse("<h1>لوحة التحكم غير موجودة</h1>")

@app.get("/audit", response_class=HTMLResponse)
def audit_page():
    p = STATIC / "audit.html"
    if p.exists(): return FileResponse(p)
    return HTMLResponse("<h1>سجل التدقيق قيد الإنشاء</h1>")

if STATIC.exists():
    app.mount("/static", StaticFiles(directory=STATIC), name="static")

import threading

@app.on_event("startup")
def startup():
    print("🚀 MAVIC starting (async reindex)...", flush=True)
    # شغّل الفحص والفهرسة في خيط منفصل حتى لا يحجب فتح المنفذ
    threading.Thread(target=_startup_reindex, daemon=True).start()
    print("✅ Startup complete - port ready", flush=True)


def _startup_reindex():
    """يعمل في الخلفية بعد فتح المنفذ"""
    import time
    time.sleep(5)  # انتظر حتى يفتح uvicorn المنفذ
    try:
        total, st = count_all()
        print(f"📚 مصادر في الملفات: {total} - {st}", flush=True)
        _init_chroma()
        from agents import _collection
        c = _collection.count() if _collection else 0
        print(f"📊 Chroma count at startup: {c}", flush=True)
        if c == 0 and total > 0:
            print("⚠️ Chroma فارغ - بدء الفهرسة في الخلفية...", flush=True)
            n, breakdown = reindex_all()
            print(f"✅ Auto reindex complete: {n} docs", flush=True)
    except Exception as e:
        print(f"⚠️ خطأ في الفهرسة: {e}", flush=True)
        traceback.print_exc()