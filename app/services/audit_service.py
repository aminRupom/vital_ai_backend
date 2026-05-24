from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditEvent
from app.models.user import User


async def record_event(
    db: AsyncSession,
    *,
    action: str,
    case_id: UUID | None = None,
    actor: User | None = None,
    details: dict | None = None,
) -> AuditEvent:
    event = AuditEvent(
        case_id=case_id,
        actor_id=actor.id if actor else None,
        actor_label=actor.email if actor else "system",
        action=action,
        details=details or {},
    )
    db.add(event)
    await db.flush()  # commit happens at the route layer
    return event


async def get_events_for_case(db: AsyncSession, case_id: UUID) -> list[AuditEvent]:
    result = await db.execute(
        select(AuditEvent).where(AuditEvent.case_id == case_id).order_by(AuditEvent.timestamp)
    )
    return list(result.scalars().all())
