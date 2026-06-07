import os
import httpx
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.dependencies import get_db
from backend.app.limiter import limiter

router = APIRouter(prefix="/health", tags=["health"])

@router.get("")
@limiter.limit("30/minute")
def health_check(request: Request, db: Session = Depends(get_db)):
    """Check health of the backend API and its dependencies (DB, Ollama, Frontier)."""
    # 1. Check Database connection
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"
        
    # 2. Check local Ollama connection
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    ollama_status = "not_configured"
    if ollama_url:
        try:
            # Pinging Ollama root endpoint
            resp = httpx.get(ollama_url, timeout=1.0)
            ollama_status = "ok" if resp.status_code == 200 else f"error: status {resp.status_code}"
        except Exception as e:
            ollama_status = f"unreachable: {str(e)}"

    # 3. Check Frontier Model setup
    frontier_model = os.getenv("FRONTIER_MODEL", "gemini-2.5-flash")
    openai_key = os.getenv("OPENAI_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")
    
    frontier_status = "missing_api_key"
    if "gemini" in frontier_model.lower():
        if google_key:
            frontier_status = "ok (configured)"
    elif openai_key:
        frontier_status = "ok (configured)"

    # Determine overall status
    is_ok = db_status == "ok" and (ollama_status == "ok" or ollama_status == "not_configured")
    status = "ok" if is_ok else "degraded"
        
    return {
        "status": status,
        "dependencies": {
            "database": db_status,
            "ollama": ollama_status,
            "frontier": frontier_status
        }
    }
