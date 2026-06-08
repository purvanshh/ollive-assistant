import json
from sqlalchemy.orm import Session
from backend.app.models import Message
from typing import List, Optional

class MessageRepository:
    @staticmethod
    def create(
        db: Session,
        conversation_id: str,
        role: str,
        content: str,
        model_used: Optional[str] = None,
        tokens_used: Optional[int] = None,
        cost_usd: Optional[float] = None,
        routing_reason: Optional[str] = None,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            model_used=model_used,
            tokens_used=tokens_used,
            cost_usd=cost_usd,
            routing_reason=routing_reason,
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message

    @staticmethod
    def list_by_conversation(db: Session, conversation_id: str) -> List[Message]:
        return (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .all()
        )

    @staticmethod
    def init_vector_table(db: Session) -> None:
        """Create the vec0 virtual table for sqlite-vec if it doesn't exist."""
        # Using connection's raw cursor since vec0 is a virtual table
        conn = db.connection().connection
        cursor = conn.cursor()
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS vec_messages USING vec0(
                message_id TEXT primary key,
                embedding float[384]
            )
        """)
        conn.commit()

    @staticmethod
    def add_embedding(db: Session, message_id: str, embedding: List[float]) -> None:
        """Store the embedding vector for a message using sqlite-vec."""
        conn = db.connection().connection
        cursor = conn.cursor()
        # Ensure sqlite-vec is loaded (in case get_db connection event didn't trigger)
        try:
            import sqlite_vec
            db.connection().enable_load_extension(True)
            sqlite_vec.load(db.connection().connection)
            db.connection().enable_load_extension(False)
        except Exception:
            pass
        
        cursor.execute(
            "INSERT OR REPLACE INTO vec_messages(message_id, embedding) VALUES (?, ?)",
            (message_id, json.dumps(embedding))
        )
        conn.commit()

    @staticmethod
    def search_similar(db: Session, query_embedding: List[float], limit: int = 3) -> List[Message]:
        """Search top-K nearest messages using vector similarity."""
        conn = db.connection().connection
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT message_id, distance
                FROM vec_messages
                WHERE embedding MATCH ?
                  AND k = ?
            """, (json.dumps(query_embedding), limit))
            rows = cursor.fetchall()
        except Exception as e:
            print(f"Warning: sqlite-vec search failed: {e}")
            return []
            
        message_ids = [row[0] for row in rows]
        if not message_ids:
            return []
            
        # Retrieve actual messages
        messages = db.query(Message).filter(Message.id.in_(message_ids)).all()
        messages_map = {msg.id: msg for msg in messages}
        
        # Return in vector search order
        return [messages_map[mid] for mid in message_ids if mid in messages_map]
