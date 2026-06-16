import uuid
from sqlalchemy import Column, String, Integer, Numeric, Boolean, DateTime, ForeignKey, Text, JSON, func
from sqlalchemy.orm import relationship
from backend.app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=False)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False)  # 'user', 'assistant', 'system', 'tool'
    content = Column(Text, nullable=False)
    model_used = Column(String(100), nullable=True)  # 'qwen', 'gemini-2.5-flash', 'blocked'
    tokens_used = Column(Integer, nullable=True)
    cost_usd = Column(Numeric(10, 6), nullable=True)
    routing_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    conversation = relationship("Conversation", back_populates="messages")
    feedbacks = relationship("Feedback", back_populates="message", cascade="all, delete-orphan")

class EvalRun(Base):
    __tablename__ = "eval_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    run_type = Column(String(50), nullable=False)  # 'full', 'smoke'
    judge_model = Column(String(100), nullable=False)
    passed = Column(Boolean, default=False)
    report_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    results = relationship("EvalResult", back_populates="eval_run", cascade="all, delete-orphan")

class EvalResult(Base):
    __tablename__ = "eval_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    eval_run_id = Column(String(36), ForeignKey("eval_runs.id", ondelete="CASCADE"), nullable=False)
    prompt_id = Column(String(100), nullable=False)
    model_a = Column(String(100), nullable=False)
    model_b = Column(String(100), nullable=False)
    winner = Column(String(10), nullable=False)  # 'a', 'b', 'tie'
    judge_reasoning = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)

    eval_run = relationship("EvalRun", back_populates="results")

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    message_id = Column(String(36), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1 = good, -1 = bad
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    message = relationship("Message", back_populates="feedbacks")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=True)
    action = Column(String(100), nullable=False)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
