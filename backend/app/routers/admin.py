from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Any, Dict
from pydantic import BaseModel
from datetime import datetime, timedelta

from backend.app.dependencies import get_db, verify_api_key
from backend.app.repositories.audit import AuditLogRepository
from backend.app.repositories.eval import EvalRepository
from backend.app.models import Message, AuditLog, Conversation, Feedback

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(verify_api_key)]
)


class CostBreakdown(BaseModel):
    date: str
    total_cost: float
    call_count: int
    oss_calls: int
    frontier_calls: int


class ModelUsage(BaseModel):
    model: str
    call_count: int
    total_cost: float


class GuardrailStats(BaseModel):
    total_checks: int
    blocked_count: int
    block_rate: float


class AuditLogEntry(BaseModel):
    id: str
    user_id: Optional[str] = None
    action: str
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardResponse(BaseModel):
    daily_costs: List[CostBreakdown]
    model_usage: List[ModelUsage]
    guardrail_stats: GuardrailStats
    total_conversations: int
    total_messages: int
    total_cost_all_time: float
    recent_audit_logs: List[AuditLogEntry]
    feedback_stats: Dict[str, Any]
    daily_budget_limit: float = 1.0
    daily_spend: float = 0.0
    budget_warning: bool = False


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(db: Session = Depends(get_db)):
    total_messages = db.query(func.count(Message.id)).scalar() or 0
    total_conversations = db.query(func.count(Conversation.id)).scalar() or 0

    total_cost = db.query(func.coalesce(func.sum(Message.cost_usd), 0)).scalar() or 0.0

    today = datetime.utcnow().date()
    today_start = datetime(today.year, today.month, today.day)
    daily_spend = db.query(
        func.coalesce(func.sum(Message.cost_usd), 0)
    ).filter(Message.created_at >= today_start).scalar() or 0.0

    budget_limit = 1.0
    budget_warning = float(daily_spend) > budget_limit

    days = 7
    daily_costs = []
    for i in range(days - 1, -1, -1):
        day = today - timedelta(days=i)
        day_start = datetime(day.year, day.month, day.day)
        day_end = day_start + timedelta(days=1)
        day_cost = db.query(
            func.coalesce(func.sum(Message.cost_usd), 0.0)
        ).filter(
            Message.created_at >= day_start,
            Message.created_at < day_end
        ).scalar() or 0.0
        day_count = db.query(func.count(Message.id)).filter(
            Message.created_at >= day_start,
            Message.created_at < day_end,
            Message.role == "assistant"
        ).scalar() or 0
        oss_count = db.query(func.count(Message.id)).filter(
            Message.created_at >= day_start,
            Message.created_at < day_end,
            Message.role == "assistant",
            Message.model_used.in_(["qwen", "oss", "Qwen/Qwen2.5-0.5B-Instruct"])
        ).scalar() or 0
        frontier_count = db.query(func.count(Message.id)).filter(
            Message.created_at >= day_start,
            Message.created_at < day_end,
            Message.role == "assistant",
            ~Message.model_used.in_(["qwen", "oss", "Qwen/Qwen2.5-0.5B-Instruct", "blocked", "error", None])
        ).scalar() or 0

        daily_costs.append(CostBreakdown(
            date=day.isoformat(),
            total_cost=round(float(day_cost), 6),
            call_count=day_count,
            oss_calls=oss_count,
            frontier_calls=frontier_count,
        ))

    model_rows = db.query(
        Message.model_used,
        func.count(Message.id).label("count"),
        func.coalesce(func.sum(Message.cost_usd), 0).label("total_cost")
    ).filter(
        Message.role == "assistant",
        Message.model_used.isnot(None)
    ).group_by(Message.model_used).order_by(func.count(Message.id).desc()).all()

    model_usage = [
        ModelUsage(
            model=row[0] or "unknown",
            call_count=row[1],
            total_cost=round(float(row[2]), 6)
        )
        for row in model_rows
    ]

    guardrail_checks = db.query(func.count(AuditLog.id)).filter(
        AuditLog.action.like("%guardrail%")
    ).scalar() or 0
    guardrail_blocks = db.query(func.count(AuditLog.id)).filter(
        AuditLog.action == "guardrail_blocked"
    ).scalar() or 0
    block_rate = round((guardrail_blocks / guardrail_checks) * 100, 1) if guardrail_checks > 0 else 0.0

    audit_logs = AuditLogRepository.list(db, skip=0, limit=10)

    all_fb = db.query(Feedback).all()
    fb_positive = sum(1 for f in all_fb if f.rating == 1)
    fb_negative = sum(1 for f in all_fb if f.rating == -1)
    fb_total = len(all_fb)

    return DashboardResponse(
        daily_costs=daily_costs,
        model_usage=model_usage,
        guardrail_stats=GuardrailStats(
            total_checks=guardrail_checks,
            blocked_count=guardrail_blocks,
            block_rate=block_rate
        ),
        total_conversations=total_conversations,
        total_messages=total_messages,
        total_cost_all_time=round(float(total_cost), 6),
        recent_audit_logs=[
            AuditLogEntry(
                id=log.id,
                user_id=log.user_id,
                action=log.action,
                details=log.details,
                ip_address=log.ip_address,
                created_at=log.created_at,
            )
            for log in audit_logs
        ],
        feedback_stats={
            "total": fb_total,
            "positive": fb_positive,
            "negative": fb_negative,
            "positive_rate": round((fb_positive / fb_total) * 100, 1) if fb_total > 0 else 0.0
        },
        daily_budget_limit=budget_limit,
        daily_spend=round(float(daily_spend), 6),
        budget_warning=budget_warning,
    )


@router.get("/audit-logs", response_model=List[AuditLogEntry])
def list_audit_logs(
    skip: int = 0,
    limit: int = 100,
    action: Optional[str] = Query(None, description="Filter by action type"),
    db: Session = Depends(get_db)
):
    logs = AuditLogRepository.list(db, skip=skip, limit=limit)
    if action:
        logs = [log for log in logs if log.action == action]
    return [
        AuditLogEntry(
            id=log.id,
            user_id=log.user_id,
            action=log.action,
            details=log.details,
            ip_address=log.ip_address,
            created_at=log.created_at,
        )
        for log in logs
    ]
