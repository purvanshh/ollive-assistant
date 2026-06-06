from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from backend.app.dependencies import get_db, verify_api_key
from backend.app.repositories.conversation import ConversationRepository
from backend.app.repositories.message import MessageRepository

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    dependencies=[Depends(verify_api_key)]
)

class ChatRequest(BaseModel):
    conversation_id: str = Field(..., description="The ID of the conversation")
    prompt: str = Field(..., min_length=1, description="The user prompt")
    model_override: Optional[str] = Field(None, description="Force a specific model (e.g. 'oss', 'frontier')")

class ChatResponse(BaseModel):
    user_message_id: str
    assistant_message_id: str
    content: str
    model_used: str
    created_at: datetime

@router.post("", response_model=ChatResponse)
def chat_completion(payload: ChatRequest, db: Session = Depends(get_db)):
    """
    Handle a user message. Saves the user prompt, generates a stub assistant response,
    saves the assistant response, and returns it.
    """
    # 1. Verify conversation exists
    conversation = ConversationRepository.get(db, payload.conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    # 2. Save user message
    user_msg = MessageRepository.create(
        db,
        conversation_id=payload.conversation_id,
        role="user",
        content=payload.prompt
    )
    
    # 3. Generate stub assistant response
    model_used = payload.model_override or "stub-model"
    response_content = f"Received prompt: '{payload.prompt}'. This is a stub response from Ollive!"
    
    # 4. Save assistant response
    asst_msg = MessageRepository.create(
        db,
        conversation_id=payload.conversation_id,
        role="assistant",
        content=response_content,
        model_used=model_used,
        tokens_used=len(response_content) // 4,
        cost_usd=0.0
    )
    
    # Update conversation title if this is the first user message
    # (sidebar auto-generated title using first 30 characters)
    messages = MessageRepository.list_by_conversation(db, payload.conversation_id)
    if len(messages) == 2:  # Just user_msg + asst_msg
        title = payload.prompt[:30]
        if len(payload.prompt) > 30:
            title += "..."
        ConversationRepository.update_title(db, payload.conversation_id, title)
        
    return ChatResponse(
        user_message_id=user_msg.id,
        assistant_message_id=asst_msg.id,
        content=response_content,
        model_used=model_used,
        created_at=asst_msg.created_at
    )
