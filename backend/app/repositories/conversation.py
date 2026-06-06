from sqlalchemy.orm import Session
from backend.app.models import Conversation
from typing import List, Optional

class ConversationRepository:
    @staticmethod
    def create(db: Session, user_id: str, title: Optional[str] = None) -> Conversation:
        conversation = Conversation(user_id=user_id, title=title)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation

    @staticmethod
    def get(db: Session, conversation_id: str) -> Optional[Conversation]:
        return db.query(Conversation).filter(Conversation.id == conversation_id).first()

    @staticmethod
    def list(db: Session, user_id: str, skip: int = 0, limit: int = 20) -> List[Conversation]:
        return (
            db.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(Conversation.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def delete(db: Session, conversation_id: str) -> bool:
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conversation:
            db.delete(conversation)
            db.commit()
            return True
        return False

    @staticmethod
    def update_title(db: Session, conversation_id: str, title: str) -> Optional[Conversation]:
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conversation:
            conversation.title = title
            db.commit()
            db.refresh(conversation)
            return conversation
        return None
