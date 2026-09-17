from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.database.models import AuditLog
from app.core.security import require_roles

router = APIRouter(prefix="/audit", tags=["Audit Logs"])

@router.get("")
def get_audit_logs(
    limit: int = 50,
    action: Optional[str] = None,
    current_user: dict = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db)
):
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    return [
        {
            "id": l.id,
            "action": l.action,
            "entity_type": l.entity_type,
            "entity_id": l.entity_id,
            "performed_by": l.performed_by,
            "details": l.details,
            "created_at": l.created_at.isoformat()
        }
        for l in logs
    ]
