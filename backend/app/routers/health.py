from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.dependencies import get_db
from backend.app.limiter import limiter

router = APIRouter(prefix="/health", tags=["health"])

@router.get("")
@limiter.limit("30/minute")
def health_check(request: Request, db: Session = Depends(get_db)):
    """Check health of the backend API and its database connection."""
    db_status = "ok"
    try:
        # Check connection
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"
        
    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "dependencies": {
            "database": db_status
        }
    }
