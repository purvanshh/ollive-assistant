import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.repositories.conversation import ConversationRepository
from backend.app.repositories.message import MessageRepository
from backend.app.repositories.feedback import FeedbackRepository
from backend.app.repositories.audit import AuditLogRepository
from backend.app.repositories.eval import EvalRepository
import sqlite3
import sqlite_vec

@pytest.fixture(name="db_session")
def fixture_db_session():
    """Sets up an in-memory SQLite database with sqlite-vec for testing."""
    engine = create_engine("sqlite:///:memory:")
    
    # Load sqlite-vec on the test connection
    @event.listens_for(engine, "connect")
    def load_extensions(dbapi_connection, connection_record):
        if isinstance(dbapi_connection, sqlite3.Connection):
            dbapi_connection.enable_load_extension(True)
            sqlite_vec.load(dbapi_connection)
            dbapi_connection.enable_load_extension(False)
            
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Initialize the vector table
    MessageRepository.init_vector_table(session)
    
    try:
        yield session
    finally:
        session.close()

def test_conversation_crud(db_session):
    # Create
    conv = ConversationRepository.create(db_session, user_id="user_123", title="Test Conversation")
    assert conv.id is not None
    assert conv.user_id == "user_123"
    assert conv.title == "Test Conversation"
    
    # Get
    retrieved = ConversationRepository.get(db_session, conv.id)
    assert retrieved is not None
    assert retrieved.title == "Test Conversation"
    
    # Update Title
    updated = ConversationRepository.update_title(db_session, conv.id, "New Title")
    assert updated.title == "New Title"
    
    # List
    convs = ConversationRepository.list(db_session, user_id="user_123")
    assert len(convs) == 1
    assert convs[0].title == "New Title"
    
    # Delete
    deleted = ConversationRepository.delete(db_session, conv.id)
    assert deleted is True
    assert ConversationRepository.get(db_session, conv.id) is None

def test_message_and_vector_search(db_session):
    conv = ConversationRepository.create(db_session, user_id="user_123")
    
    # Create message
    msg = MessageRepository.create(
        db_session,
        conversation_id=conv.id,
        role="user",
        content="What is the capital of France?",
        model_used="gemini-2.5-flash",
        tokens_used=10,
        cost_usd=0.0001
    )
    assert msg.id is not None
    assert msg.content == "What is the capital of France?"
    
    # Add embedding
    embedding = [0.1] * 384
    MessageRepository.add_embedding(db_session, msg.id, embedding)
    
    # Search similar (should find it)
    results = MessageRepository.search_similar(db_session, query_embedding=[0.09] * 384, limit=1)
    assert len(results) == 1
    assert results[0].id == msg.id
    assert results[0].content == msg.content

def test_feedback_crud(db_session):
    conv = ConversationRepository.create(db_session, user_id="user_123")
    msg = MessageRepository.create(db_session, conversation_id=conv.id, role="assistant", content="Response")
    
    fb = FeedbackRepository.create(db_session, message_id=msg.id, rating=1, comment="Great answer!")
    assert fb.id is not None
    assert fb.rating == 1
    assert fb.comment == "Great answer!"
    
    fbs = FeedbackRepository.list(db_session)
    assert len(fbs) == 1
    assert fbs[0].comment == "Great answer!"

def test_audit_logs(db_session):
    log = AuditLogRepository.create(
        db_session,
        action="user_login",
        user_id="user_123",
        details={"browser": "chrome"},
        ip_address="127.0.0.1"
    )
    assert log.id is not None
    assert log.action == "user_login"
    assert log.details == {"browser": "chrome"}
    
    logs = AuditLogRepository.list(db_session)
    assert len(logs) == 1
    assert logs[0].ip_address == "127.0.0.1"

def test_eval_suite(db_session):
    run = EvalRepository.create_run(
        db_session,
        run_type="smoke",
        judge_model="gpt-4.1-mini",
        passed=True,
        report_path="/reports/1.md"
    )
    assert run.id is not None
    assert run.passed is True
    
    result = EvalRepository.create_result(
        db_session,
        eval_run_id=run.id,
        prompt_id="prompt_01",
        model_a="qwen",
        model_b="gemini",
        winner="tie",
        judge_reasoning="Both were fine."
    )
    assert result.id is not None
    
    results = EvalRepository.list_results_for_run(db_session, run.id)
    assert len(results) == 1
    assert results[0].prompt_id == "prompt_01"
