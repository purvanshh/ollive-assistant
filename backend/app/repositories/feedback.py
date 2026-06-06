from sqlalchemy.orm import Session
from backend.app.models import Feedback
from typing import List, Optional

class FeedbackRepository:
    @staticmethod
    def create(db: Session, message_id: str, rating: int, comment: Optional[str] = None) -> Feedback:
        feedback = Feedback(message_id=message_id, rating=rating, comment=comment)
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        return feedback

    @staticmethod
    def list(db: Session, skip: int = 0, limit: int = 100) -> List[Feedback]:
        return (
            db.query(Feedback)
            .order_by(Feedback.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
