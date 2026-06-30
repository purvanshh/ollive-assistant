import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.repositories.eval import EvalRepository
from evaluation.generate_pdf import generate_pdf_report

# Setup test client and DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(name="db_session")
def fixture_db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

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

def test_pdf_generation_success(db_session):
    # 1. Create a dummy evaluation run in the test DB
    run = EvalRepository.create_run(
        db=db_session,
        run_type="smoke",
        judge_model="gpt-4.1-mini",
        passed=True,
        report_path="/dummy/path.json"
    )
    
    # 2. Create detailed results
    details = {
        "category": "factual",
        "dimension": "factual_accuracy",
        "prompt": "What is the capital of France?",
        "model_a": {
            "name": "oss",
            "response": "Paris.",
            "score": 5,
            "justification": "Exactly correct.",
            "latency_ms": 120.0,
        },
        "model_b": {
            "name": "frontier",
            "response": "The capital is Paris.",
            "score": 5,
            "justification": "Correct and helpful.",
            "latency_ms": 400.0,
        }
    }
    
    EvalRepository.create_result(
        db=db_session,
        eval_run_id=run.id,
        prompt_id="factual_1",
        model_a="oss",
        model_b="frontier",
        winner="tie",
        judge_reasoning="Both answered Paris correctly.",
        details=details
    )

    # 3. Trigger PDF report generator
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        pdf_path = tmp.name
        
    try:
        generate_pdf_report(run.id, db_session, pdf_path)
        assert os.path.exists(pdf_path)
        assert os.path.getsize(pdf_path) > 1000  # Verify PDF is populated and not empty
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

def test_pdf_endpoint_success(client, db_session):
    # 1. Create a dummy evaluation run in the test DB
    run = EvalRepository.create_run(
        db=db_session,
        run_type="smoke",
        judge_model="gpt-4.1-mini",
        passed=True,
        report_path="/dummy/path.json"
    )
    
    # 2. Create detailed results
    details = {
        "category": "factual",
        "dimension": "factual_accuracy",
        "prompt": "What is the capital of France?",
        "model_a": {
            "name": "oss",
            "score": 5,
            "justification": "Exactly correct.",
        },
        "model_b": {
            "name": "frontier",
            "score": 5,
            "justification": "Correct.",
        }
    }
    
    EvalRepository.create_result(
        db=db_session,
        eval_run_id=run.id,
        prompt_id="factual_1",
        model_a="oss",
        model_b="frontier",
        winner="tie",
        judge_reasoning="Both answered Paris correctly.",
        details=details
    )

    # 3. Call HTTP endpoint to download PDF (with valid API Key header)
    headers = {"X-API-Key": "test_api_key_12345"}
    response = client.get(f"/api/v1/evaluations/runs/{run.id}/pdf", headers=headers)
    
    assert response.status_code == 200
    assert response.headers.get("content-type") == "application/pdf"
    assert f"ollive_eval_report_{run.id}.pdf" in response.headers.get("content-disposition", "")
    assert len(response.content) > 1000  # Response body contains valid PDF bytes
