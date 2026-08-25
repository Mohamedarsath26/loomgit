from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from loomgit import Memory

app = FastAPI(title="loomgit Local Dashboard", version="0.1.0")

_memory_instance: Optional[Memory] = None

def get_memory_instance() -> Memory:
    global _memory_instance
    if _memory_instance is None:
        db_dir = Path.home() / ".loomgit"
        db_dir.mkdir(parents=True, exist_ok=True)
        db_path = db_dir / "store.db"
        legacy_db_path = Path.home() / ".devloom" / "store.db"
        if not db_path.exists() and legacy_db_path.exists():
            import shutil
            try:
                shutil.copy2(legacy_db_path, db_path)
            except Exception:
                pass
        _memory_instance = Memory(db_path=db_path)
    return _memory_instance

class LogMemoryRequest(BaseModel):
    message: str

@app.get("/", response_class=HTMLResponse)
def get_dashboard():
    """Serves the single-page web dashboard interface."""
    html_file = Path(__file__).parent / "dashboard.html"
    if not html_file.exists():
        raise HTTPException(status_code=440, detail="Dashboard template not found.")
    return html_file.read_text(encoding="utf-8")

@app.get("/logo.png")
def get_logo():
    """Serves the loomgit brand logo image."""
    from fastapi.responses import FileResponse
    logo_path = Path(__file__).parent / "logo.png"
    if logo_path.exists():
        return FileResponse(logo_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Logo image not found.")

@app.get("/api/projects")
def list_projects():
    """Returns a list of unique project folders stored in memory."""
    memory = get_memory_instance()
    return memory.store.get_unique_projects()

@app.get("/api/memories")
def list_memories(limit: int = 50, type: Optional[str] = None, project_path: Optional[str] = None):
    """Returns chronological memory records."""
    memory = get_memory_instance()
    records = memory.list_all(limit=limit, order="DESC", project_path=project_path)
    
    output = []
    for r in records:
        if type and type.upper() != "ALL" and r.type.value.lower() != type.lower():
            continue
        output.append({
            "id": r.id,
            "type": r.type.value,
            "summary": r.summary,
            "what_changed": r.what_changed,
            "reasoning": r.reasoning,
            "tags": r.tags,
            "related_files": r.related_files,
            "timestamp": r.timestamp.isoformat(),
            "source_ref": r.source_ref,
            "project_name": r.project_name,
            "project_path": r.project_path,
        })
    return output

@app.get("/api/search")
def search_memories(q: str, limit: int = 15, project_path: Optional[str] = None):
    """Performs semantic vector search across developer memories."""
    if not q or not q.strip():
        return list_memories(limit=limit, project_path=project_path)
        
    memory = get_memory_instance()
    results = memory.search(query=q.strip(), limit=limit, project_path=project_path)
    
    output = []
    for r in results:
        output.append({
            "id": r.id,
            "type": r.type.value,
            "summary": r.summary,
            "what_changed": r.what_changed,
            "reasoning": r.reasoning,
            "tags": r.tags,
            "related_files": r.related_files,
            "timestamp": r.timestamp.isoformat(),
            "source_ref": r.source_ref,
            "project_name": r.project_name,
            "project_path": r.project_path,
        })
    return output

@app.get("/api/stats")
def get_stats(project_path: Optional[str] = None):
    """Calculates dashboard analytics and metrics."""
    memory = get_memory_instance()
    records = memory.list_all(limit=500, project_path=project_path)
    
    total_memories = len(records)
    type_counts = {}
    files_set = set()
    tags_set = set()

    for r in records:
        t = r.type.value
        type_counts[t] = type_counts.get(t, 0) + 1
        
        for f in r.related_files:
            files_set.add(f)
            
        for tag in r.tags:
            tags_set.add(tag)

    top_category = max(type_counts, key=type_counts.get) if type_counts else "None"

    return {
        "total_memories": total_memories,
        "top_category": top_category,
        "type_counts": type_counts,
        "top_files_count": len(files_set),
        "top_tags_count": len(tags_set),
    }

@app.post("/api/log")
def log_manual_memory(req: LogMemoryRequest):
    """Captures a manual memory and processes it with AI."""
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
        
    memory = get_memory_instance()
    memory.capture(source="manual", raw_text=req.message.strip())
    return {"status": "success", "message": "Memory captured successfully."}

@app.get("/api/memories/{record_id}")
def get_memory(record_id: str):
    """Retrieves a single memory record by its ID."""
    memory = get_memory_instance()
    r = memory.store.get_memory_record(record_id)
    if not r:
        raise HTTPException(status_code=404, detail="Memory record not found.")
    return {
        "id": r.id,
        "type": r.type.value,
        "summary": r.summary,
        "what_changed": r.what_changed,
        "reasoning": r.reasoning,
        "tags": r.tags,
        "related_files": r.related_files,
        "timestamp": r.timestamp.isoformat(),
        "source_ref": r.source_ref,
        "project_name": r.project_name,
        "project_path": r.project_path,
    }

@app.delete("/api/memories/{record_id}")
def delete_memory(record_id: str):
    """Deletes a single memory record by its ID."""
    memory = get_memory_instance()
    deleted = memory.delete(record_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory record not found.")
    return {"status": "success", "message": "Memory record deleted successfully."}

