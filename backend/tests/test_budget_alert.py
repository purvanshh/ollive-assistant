import os
import json
import pytest
import sqlite3
import sqlite_vec
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.repositories.conversation import ConversationRepository
from backend.app.repositories.message import MessageRepository

# Setup test DB path
TEST_DB_PATH = "./test_budget_temp.db"

@pytest.fixture(name="db_session")
def fixture_db_session():
    """Sets up a temporary file-based SQLite database with sqlite-vec for testing."""
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass

    engine = create_engine(f"sqlite:///{TEST_DB_PATH}", connect_args={"check_same_thread": False})
    
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
        if os.path.exists(TEST_DB_PATH):
            try:
                os.remove(TEST_DB_PATH)
            except Exception:
                pass

@pytest.fixture(name="client")
def fixture_client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@patch("backend.app.routers.chat.logger")
def test_budget_alert_warning_logged(mock_logger, client, db_session):
    # Set headers
    headers = {"X-API-Key": "test_api_key_12345"}
    os.environ["API_KEY"] = "test_api_key_12345"

    # 1. Create conversation
    conv = ConversationRepository.create(db_session, user_id="test_user", title="Budget Test")
    
    # 2. Add a message to DB with a cost that exceeds $1.00 (e.g. $1.50)
    MessageRepository.create(
        db_session,
        conversation_id=conv.id,
        role="assistant",
        content="Expensive past reply",
        model_used="frontier",
        tokens_used=1000,
        cost_usd=1.50
    )
    
    # 3. Call chat endpoint (this will create another message, which totals to > $1.00)
    # Use simple prompt that routes to local model (OSS) so it completes immediately offline
    chat_response = client.post(
        "/api/v1/chat",
        json={"conversation_id": conv.id, "prompt": "Hi, simple test!"},
        headers=headers
    )
    
    assert chat_response.status_code == 200
    # Read the stream to force completion of generator
    list(chat_response.iter_lines())
    
    # 4. Verify that logger.warning was called at least once
    assert mock_logger.warning.called
    # Check that warning content includes the event name
    args, kwargs = mock_logger.warning.call_args
    log_json = json.loads(args[0])
    assert log_json["event"] == "budget_limit_exceeded"
    assert log_json["daily_spend"] >= 1.50
    assert log_json["budget_limit"] == 1.0
