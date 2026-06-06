from sqlalchemy.orm import Session
from backend.app.models import EvalRun, EvalResult
from typing import List, Optional

class EvalRepository:
    @staticmethod
    def create_run(
        db: Session,
        run_type: str,
        judge_model: str,
        passed: bool = False,
        report_path: Optional[str] = None,
    ) -> EvalRun:
        eval_run = EvalRun(
            run_type=run_type,
            judge_model=judge_model,
            passed=passed,
            report_path=report_path,
        )
        db.add(eval_run)
        db.commit()
        db.refresh(eval_run)
        return eval_run

    @staticmethod
    def get_run(db: Session, run_id: str) -> Optional[EvalRun]:
        return db.query(EvalRun).filter(EvalRun.id == run_id).first()

    @staticmethod
    def list_runs(db: Session, skip: int = 0, limit: int = 100) -> List[EvalRun]:
        return (
            db.query(EvalRun)
            .order_by(EvalRun.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def create_result(
        db: Session,
        eval_run_id: str,
        prompt_id: str,
        model_a: str,
        model_b: str,
        winner: str,
        judge_reasoning: str,
    ) -> EvalResult:
        eval_result = EvalResult(
            eval_run_id=eval_run_id,
            prompt_id=prompt_id,
            model_a=model_a,
            model_b=model_b,
            winner=winner,
            judge_reasoning=judge_reasoning,
        )
        db.add(eval_result)
        db.commit()
        db.refresh(eval_result)
        return eval_result

    @staticmethod
    def list_results_for_run(db: Session, eval_run_id: str) -> List[EvalResult]:
        return (
            db.query(EvalResult)
            .filter(EvalResult.eval_run_id == eval_run_id)
            .all()
        )
