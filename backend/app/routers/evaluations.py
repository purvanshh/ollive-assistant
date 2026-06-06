from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime

from backend.app.dependencies import get_db, verify_api_key
from backend.app.repositories.eval import EvalRepository

router = APIRouter(
    prefix="/evaluations",
    tags=["evaluations"],
    dependencies=[Depends(verify_api_key)]
)

# Schemas
class EvalRunResponse(BaseModel):
    id: str
    run_type: str
    judge_model: str
    passed: bool
    report_path: datetime | str | None
    created_at: datetime

    class Config:
        from_attributes = True

class EvalResultResponse(BaseModel):
    id: str
    eval_run_id: str
    prompt_id: str
    model_a: str
    model_b: str
    winner: str
    judge_reasoning: str

    class Config:
        from_attributes = True

# Routes
@router.get("/runs", response_model=List[EvalRunResponse])
def list_eval_runs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all past evaluation runs."""
    return EvalRepository.list_runs(db, skip=skip, limit=limit)

@router.get("/runs/{run_id}", response_model=EvalRunResponse)
def get_eval_run(run_id: str, db: Session = Depends(get_db)):
    """Retrieve details of a specific evaluation run."""
    run = EvalRepository.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Evaluation run not found")
    return run

@router.get("/runs/{run_id}/results", response_model=List[EvalResultResponse])
def get_eval_run_results(run_id: str, db: Session = Depends(get_db)):
    """Retrieve all prompt-level results for a specific evaluation run."""
    # Check if run exists
    run = EvalRepository.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Evaluation run not found")
    return EvalRepository.list_results_for_run(db, run_id)
