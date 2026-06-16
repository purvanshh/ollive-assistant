from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from backend.app.dependencies import get_db, verify_api_key
from backend.app.repositories.feedback import FeedbackRepository
from backend.app.repositories.message import MessageRepository

router = APIRouter(
    prefix="/feedback",
    tags=["feedback"],
    dependencies=[Depends(verify_api_key)]
)


class FeedbackCreate(BaseModel):
    message_id: str
    rating: int  # 1 = good, -1 = bad
    comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: str
    message_id: str
    rating: int
    comment: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FeedbackStats(BaseModel):
    total_feedback: int
    positive: int
    negative: int
    positive_rate: float


@router.post("", response_model=FeedbackResponse)
def create_feedback(body: FeedbackCreate, db: Session = Depends(get_db)):
    message = MessageRepository.get_by_id(db, body.message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    if body.rating not in (1, -1):
        raise HTTPException(status_code=400, detail="Rating must be 1 (good) or -1 (bad)")
    return FeedbackRepository.create(db, message_id=body.message_id, rating=body.rating, comment=body.comment)


@router.get("", response_model=List[FeedbackResponse])
def list_feedback(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return FeedbackRepository.list(db, skip=skip, limit=limit)


@router.get("/stats", response_model=FeedbackStats)
def get_feedback_stats(db: Session = Depends(get_db)):
    all_fb = FeedbackRepository.list(db, skip=0, limit=100000)
    positive = sum(1 for f in all_fb if f.rating == 1)
    negative = sum(1 for f in all_fb if f.rating == -1)
    total = len(all_fb)
    return FeedbackStats(
        total_feedback=total,
        positive=positive,
        negative=negative,
        positive_rate=round((positive / total) * 100, 1) if total > 0 else 0.0
    )
