"""Rules-based triage classifier — Phase 1.

In Phase 3 this will be replaced by an NLP urgency classifier behind a
LangGraph node, and the abstraction will move to app.agents.triage.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.triage import TriageCategory, TriageResult
from app.models.user import User
from app.schemas.enums import RoutingAction
from app.schemas.triage import TriageRequest, TriageResponse
from app.services.audit_service import record_event

URGENT_KEYWORDS: tuple[str, ...] = (
    "emergency",
    "urgent",
    "immediate",
    "critical",
    "chest pain",
    "difficulty breathing",
    "unconscious",
)

TIME_SENSITIVE_KEYWORDS: tuple[str, ...] = (
    "today",
    "asap",
    "soon",
    "worried",
    "concerned",
    "follow-up",
    "test results",
    "referral",
)


def _matches_any(text: str, keywords: tuple[str, ...]) -> bool:
    """Substring match — handles multi-word phrases like 'chest pain'."""
    return any(kw in text for kw in keywords)


# Phase 3: replace with app.agents.triage_agent.classify_with_graph (LangGraph orchestration)
async def classify(db: AsyncSession, request: TriageRequest, actor: User) -> TriageResponse:
    haystack = request.contact_reason.lower() + " " + " ".join(k.lower() for k in request.keywords)

    has_urgent = _matches_any(haystack, URGENT_KEYWORDS)
    has_time_sensitive = _matches_any(haystack, TIME_SENSITIVE_KEYWORDS)
    has_patient_flags = len(request.patient_priority_flags) > 0
    insufficient_info = len(haystack.split()) < 3

    # Patient priority flags escalate; they do not reduce confidence.
    if has_urgent or (has_patient_flags and has_time_sensitive):
        category = TriageCategory.IMMEDIATE
        confidence = 0.9
        rationale = "Urgent keyword or flagged-patient + time-sensitive — immediate escalation"
        routing_action = RoutingAction.DIRECT_ESCALATION
        target_queue = "escalation_immediate"
        escalated = True
    elif has_time_sensitive or has_patient_flags:
        category = TriageCategory.TIME_SENSITIVE
        confidence = 0.7
        rationale = "Time-sensitive keyword or patient priority flag — human review"
        routing_action = RoutingAction.HUMAN_REVIEW
        target_queue = "priority_review"
        escalated = True
    elif insufficient_info:
        category = TriageCategory.LOW_CONFIDENCE
        confidence = 0.4
        rationale = "Insufficient information — manual review required"
        routing_action = RoutingAction.HUMAN_REVIEW
        target_queue = "low_confidence_review"
        escalated = True
    else:
        category = TriageCategory.ROUTINE
        confidence = 0.8
        rationale = "Routine administrative matter — normal workflow"
        routing_action = RoutingAction.ADMIN_WORKFLOW
        target_queue = "admin_routine"
        escalated = False

    triage_row = TriageResult(
        case_id=request.case_id,
        category=category,
        confidence=confidence,
        rationale=rationale,
    )
    db.add(triage_row)
    await db.flush()

    await record_event(
        db,
        case_id=request.case_id,
        actor=actor,
        action="triage.performed",
        details={
            "triage_id": str(triage_row.id),
            "category": category.value,
            "confidence": confidence,
            "escalated": escalated,
        },
    )
    await db.commit()
    await db.refresh(triage_row)

    return TriageResponse(
        triage_id=triage_row.id,
        case_id=request.case_id,
        category=category,
        confidence=confidence,
        rationale=rationale,
        routing_action=routing_action,
        target_queue=target_queue,
        escalated=escalated,
    )
