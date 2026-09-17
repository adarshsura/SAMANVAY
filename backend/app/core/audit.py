import datetime
from sqlalchemy.orm import Session
from app.database.models import AuditLog

def record_audit_log(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: str,
    performed_by: str,
    details: dict = None
):
    try:
        log_entry = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            performed_by=performed_by,
            details=details or {},
            created_at=datetime.datetime.utcnow()
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[AUDIT ERROR] Failed to record audit log: {e}")
