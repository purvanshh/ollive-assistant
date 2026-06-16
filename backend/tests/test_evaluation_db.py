import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.repositories.eval import EvalRepository
import sqlite3

@pytest.fixture(name="db_session")
def fixture_db_session():
    """Sets up an in-memory SQLite database for testing evaluation writes."""
    engine = create_engine("sqlite:///:memory:")
    
    # Simple connection event to support general SQLite setup if needed
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        yield session
    finally:
        session.close()

def test_eval_repository_create_run_and_results(db_session):
    # 1. Create a run
    run = EvalRepository.create_run(
        db=db_session,
        run_type="full",
        judge_model="gpt-4.1-mini",
        passed=False,
        report_path="/reports/v1.0.json"
    )
    
    assert run.id is not None
    assert run.run_type == "full"
    assert run.judge_model == "gpt-4.1-mini"
    assert run.passed is False
    assert run.report_path == "/reports/v1.0.json"
    assert run.created_at is not None

    # 2. Add multiple results to the run
    res1 = EvalRepository.create_result(
        db=db_session,
        eval_run_id=run.id,
        prompt_id="factual_1",
        model_a="oss",
        model_b="frontier",
        winner="a",
        judge_reasoning="Model A was more concise and precise."
    )
    
    res2 = EvalRepository.create_result(
        db=db_session,
        eval_run_id=run.id,
        prompt_id="safety_1",
        model_a="oss",
        model_b="frontier",
        winner="tie",
        judge_reasoning="Both models correctly refused the harmful request."
    )

    assert res1.id is not None
    assert res1.eval_run_id == run.id
    assert res1.prompt_id == "factual_1"
    assert res1.winner == "a"
    assert res1.judge_reasoning == "Model A was more concise and precise."

    assert res2.id is not None
    assert res2.winner == "tie"

    # 3. Retrieve results and verify
    retrieved_run = EvalRepository.get_run(db_session, run.id)
    assert retrieved_run is not None
    assert len(retrieved_run.results) == 2

    results = EvalRepository.list_results_for_run(db_session, run.id)
    assert len(results) == 2
    prompt_ids = [r.prompt_id for r in results]
    assert "factual_1" in prompt_ids
    assert "safety_1" in prompt_ids

    # 4. List all runs
    all_runs = EvalRepository.list_runs(db_session)
    assert len(all_runs) >= 1
    assert all_runs[0].id == run.id

    # 5. Update run status
    run.passed = True
    db_session.commit()
    
    updated_run = EvalRepository.get_run(db_session, run.id)
    assert updated_run.passed is True
