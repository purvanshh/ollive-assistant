from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from backend.app.dependencies import get_db, verify_api_key
from backend.app.repositories.conversation import ConversationRepository
from backend.app.repositories.message import MessageRepository

router = APIRouter(
    prefix="/conversations",
    tags=["conversations"],
    dependencies=[Depends(verify_api_key)]
)

# Schemas
class ConversationCreate(BaseModel):
    user_id: str = Field(..., description="Unique identifier for the user")
    title: Optional[str] = Field(None, description="Optional title for the conversation")

class ConversationUpdateTitle(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="New title of the conversation")

class ConversationResponse(BaseModel):
    id: str
    user_id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    model_used: Optional[str]
    tokens_used: Optional[int]
    cost_usd: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True

# Routes
@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(payload: ConversationCreate, db: Session = Depends(get_db)):
    """Create a new conversation."""
    return ConversationRepository.create(db, user_id=payload.user_id, title=payload.title)

@router.get("", response_model=List[ConversationResponse])
def list_conversations(user_id: str, skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """List conversations for a given user with pagination."""
    return ConversationRepository.list(db, user_id=user_id, skip=skip, limit=limit)

@router.get("/{conversation_id}", response_model=ConversationResponse)
def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Retrieve details of a specific conversation."""
    conversation = ConversationRepository.get(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation

@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Delete a conversation and all its messages."""
    success = ConversationRepository.delete(db, conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return

@router.put("/{conversation_id}/title", response_model=ConversationResponse)
def update_conversation_title(conversation_id: str, payload: ConversationUpdateTitle, db: Session = Depends(get_db)):
    """Update the title of an existing conversation."""
    conversation = ConversationRepository.update_title(db, conversation_id, payload.title)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation

@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
def get_conversation_messages(conversation_id: str, db: Session = Depends(get_db)):
    """Retrieve all messages belonging to a conversation."""
    # Check if conversation exists first
    conversation = ConversationRepository.get(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return MessageRepository.list_by_conversation(db, conversation_id)
