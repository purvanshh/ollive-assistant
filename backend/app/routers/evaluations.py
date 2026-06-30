from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Any, Dict
from pydantic import BaseModel
from datetime import datetime

from backend.app.dependencies import get_db, verify_api_key
from backend.app.repositories.eval import EvalRepository

router = APIRouter(
    prefix="/evaluations",
    tags=["evaluations"],
    dependencies=[Depends(verify_api_key)]
)


class EvalRunResponse(BaseModel):
    id: str
    run_type: str
    judge_model: str
    passed: bool
    report_path: Optional[str] = None
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
    details: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class TriggerEvalRequest(BaseModel):
    model_a: str = "oss"
    model_b: str = "frontier"
    judge_model: str = "gpt-4.1-mini"
    run_type: str = "smoke"


class TriggerEvalResponse(BaseModel):
    run_id: str
    message: str


class DimensionScore(BaseModel):
    category: str
    dimension: str
    model_a_avg_score: float
    model_b_avg_score: float
    model_a_win_count: int
    model_b_win_count: int
    tie_count: int
    prompt_count: int


class RunStatsResponse(BaseModel):
    run_id: str
    run_type: str
    judge_model: str
    passed: bool
    created_at: datetime
    total_prompts: int
    model_a_name: str
    model_b_name: str
    model_a_wins: int
    model_b_wins: int
    ties: int
    dimension_scores: List[DimensionScore]


class OverallStatsResponse(BaseModel):
    total_runs: int
    completed_runs: int
    active_models: List[str]
    overall_model_a_win_rate: float
    overall_model_b_win_rate: float
    overall_tie_rate: float
    recent_runs: List[EvalRunResponse]


def _compute_run_stats(run, results) -> RunStatsResponse:
    dimension_scores: Dict[str, Dict[str, Any]] = {}
    model_a_wins = 0
    model_b_wins = 0
    ties = 0

    for r in results:
        if r.winner == "a":
            model_a_wins += 1
        elif r.winner == "b":
            model_b_wins += 1
        else:
            ties += 1

        details = r.details or {}
        category = details.get("category", r.prompt_id.rsplit("_", 1)[0])
        dimension = details.get("dimension", "unknown")
        key = f"{category}_{dimension}"

        if key not in dimension_scores:
            dimension_scores[key] = {
                "category": category,
                "dimension": dimension,
                "model_a_scores": [],
                "model_b_scores": [],
                "model_a_wins": 0,
                "model_b_wins": 0,
                "ties": 0,
            }

        ma = details.get("model_a", {})
        mb = details.get("model_b", {})
        score_a = ma.get("score")
        score_b = mb.get("score")

        if isinstance(score_a, (int, float)):
            dimension_scores[key]["model_a_scores"].append(score_a)
        if isinstance(score_b, (int, float)):
            dimension_scores[key]["model_b_scores"].append(score_b)

        if r.winner == "a":
            dimension_scores[key]["model_a_wins"] += 1
        elif r.winner == "b":
            dimension_scores[key]["model_b_wins"] += 1
        else:
            dimension_scores[key]["ties"] += 1

    dim_scores_list = []
    for key, data in sorted(dimension_scores.items()):
        a_scores = data["model_a_scores"]
        b_scores = data["model_b_scores"]
        dim_scores_list.append(
            DimensionScore(
                category=data["category"],
                dimension=data["dimension"],
                model_a_avg_score=round(sum(a_scores) / len(a_scores), 2) if a_scores else 0.0,
                model_b_avg_score=round(sum(b_scores) / len(b_scores), 2) if b_scores else 0.0,
                model_a_win_count=data["model_a_wins"],
                model_b_win_count=data["model_b_wins"],
                tie_count=data["ties"],
                prompt_count=len(a_scores) + len(b_scores) - len(a_scores),
            )
        )
        dim_scores_list[-1].prompt_count = max(len(a_scores), len(b_scores))

    model_a_name = results[0].model_a if results else "unknown"
    model_b_name = results[0].model_b if results else "unknown"

    return RunStatsResponse(
        run_id=run.id,
        run_type=run.run_type,
        judge_model=run.judge_model,
        passed=run.passed,
        created_at=run.created_at,
        total_prompts=len(results),
        model_a_name=model_a_name,
        model_b_name=model_b_name,
        model_a_wins=model_a_wins,
        model_b_wins=model_b_wins,
        ties=ties,
        dimension_scores=dim_scores_list,
    )


@router.get("/runs", response_model=List[EvalRunResponse])
def list_eval_runs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return EvalRepository.list_runs(db, skip=skip, limit=limit)


@router.get("/runs/{run_id}", response_model=EvalRunResponse)
def get_eval_run(run_id: str, db: Session = Depends(get_db)):
    run = EvalRepository.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Evaluation run not found")
    return run


@router.get("/runs/{run_id}/results", response_model=List[EvalResultResponse])
def get_eval_run_results(run_id: str, db: Session = Depends(get_db)):
    run = EvalRepository.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Evaluation run not found")
    return EvalRepository.list_results_for_run(db, run_id)


@router.get("/runs/{run_id}/stats", response_model=RunStatsResponse)
def get_eval_run_stats(run_id: str, db: Session = Depends(get_db)):
    run = EvalRepository.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Evaluation run not found")
    results = EvalRepository.list_results_for_run(db, run_id)
    return _compute_run_stats(run, results)


@router.post("/runs", response_model=TriggerEvalResponse)
def trigger_evaluation(
    request: TriggerEvalRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    import sys
    from pathlib import Path

    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    def _run_eval_bg():
        from evaluation.run_eval import run_evaluation_params
        run_evaluation_params(
            model_a_name=request.model_a,
            model_b_name=request.model_b,
            judge_model_name=request.judge_model,
            run_type=request.run_type,
        )

    background_tasks.add_task(_run_eval_bg)
    return TriggerEvalResponse(
        run_id="pending",
        message=f"Evaluation triggered in background. Run type: {request.run_type}. Judge: {request.judge_model}."
    )


@router.get("/stats", response_model=OverallStatsResponse)
def get_overall_stats(db: Session = Depends(get_db)):
    all_runs = EvalRepository.list_runs(db, skip=0, limit=1000)
    completed = [r for r in all_runs if r.passed]

    models_set = set()
    total_a_wins = 0
    total_b_wins = 0
    total_ties = 0
    total_results = 0

    for run in completed[:10]:
        results = EvalRepository.list_results_for_run(db, run.id)
        for r in results:
            models_set.add(r.model_a)
            models_set.add(r.model_b)
            if r.winner == "a":
                total_a_wins += 1
            elif r.winner == "b":
                total_b_wins += 1
            else:
                total_ties += 1
            total_results += 1

    if total_results > 0:
        a_rate = round((total_a_wins / total_results) * 100, 1)
        b_rate = round((total_b_wins / total_results) * 100, 1)
        tie_rate = round((total_ties / total_results) * 100, 1)
    else:
        a_rate = b_rate = tie_rate = 0.0

    recent = [
        EvalRunResponse(
            id=r.id,
            run_type=r.run_type,
            judge_model=r.judge_model,
            passed=r.passed,
            report_path=r.report_path,
            created_at=r.created_at,
        )
        for r in all_runs[:5]
    ]

    return OverallStatsResponse(
        total_runs=len(all_runs),
        completed_runs=len(completed),
        active_models=sorted(models_set) if models_set else ["oss", "frontier"],
        overall_model_a_win_rate=a_rate,
        overall_model_b_win_rate=b_rate,
        overall_tie_rate=tie_rate,
        recent_runs=recent,
    )


@router.get("/runs/{run_id}/pdf")
def get_eval_run_pdf(run_id: str, db: Session = Depends(get_db)):
    """Generate and download a professional PDF report for a run."""
    run = EvalRepository.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Evaluation run not found")
    
    import os
    import tempfile
    from evaluation.generate_pdf import generate_pdf_report
    from fastapi.responses import FileResponse

    fd, pdf_path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)

    try:
        generate_pdf_report(run_id, db, pdf_path)
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=f"ollive_eval_report_{run_id}.pdf"
        )
    except Exception as e:
        if os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {e}")
