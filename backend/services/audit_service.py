from sqlalchemy.orm import Session

from core.config import get_settings
from db.models import AuditLogEntry


def log(
    db: Session,
    *,
    action: str,
    document_id: str | None = None,
    detail: dict | None = None,
    user_approved: bool | None = None,
) -> None:
    db.add(
        AuditLogEntry(
            document_id=document_id,
            action=action,
            detail=detail or {},
            user_approved=user_approved,
            ollama_mode=get_settings().OLLAMA_MODE,
        )
    )
    db.commit()
