from sqlalchemy.orm import Session
from backend.app.models import AuditLog
from typing import List, Optional, Any, Dict

class AuditLogRepository:
    @staticmethod
    def create(
        db: Session,
        action: str,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            details=details,
            ip_address=ip_address,
        )
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        return audit_log

    @staticmethod
    def list(db: Session, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        return (
            db.query(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
