import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_request_language, require_roles
from app.db.session import get_db
from app.i18n import t
from app.models.douar import Douar
from app.models.enums import (
    AuditAction,
    NotificationType,
    ReportStatus,
    UserRole,
    ValidationDecision,
)
from app.models.report import Report
from app.models.user import User
from app.models.validation import Validation
from app.schemas.validations import ValidationCreate, ValidationCreateOut
from app.services.audit import write_audit_log
from app.services.notifications import notify_all_managers, notify_user
from app.services.priority import get_active_scoring_config, recompute_priority
from app.services.territory_scope import territory_scope_filter

router = APIRouter(prefix="/reports", tags=["validations"])

_require_expert = require_roles(UserRole.EXPERT)

# A decision that approves the report (with or without modifications)
# moves it to `validated`; only these two produce a new report status.
_DECISION_TO_STATUS = {
    ValidationDecision.VALIDATED: ReportStatus.VALIDATED,
    ValidationDecision.MODIFIED: ReportStatus.VALIDATED,
    ValidationDecision.RECHECK_REQUESTED: ReportStatus.RECHECK_REQUESTED,
    ValidationDecision.REJECTED: ReportStatus.REJECTED,
}

_TERMINAL_STATUSES = {ReportStatus.REJECTED, ReportStatus.CONVERTED_TO_PROJECT}


@router.post(
    "/{report_id}/validations",
    response_model=ValidationCreateOut,
    status_code=status.HTTP_201_CREATED,
)
def create_validation(
    report_id: uuid.UUID,
    body: ValidationCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_expert),
) -> ValidationCreateOut:
    lang = get_request_language(request)
    scope = territory_scope_filter(Douar.commune_id, db, current_user)
    report = (
        db.query(Report)
        .join(Douar, Report.douar_id == Douar.id)
        .filter(Report.id == report_id, scope)
        .first()
    )
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=t("errors.not_found", lang)
        )
    if report.status in _TERMINAL_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=t("errors.invalid_status_transition", lang),
        )

    validation = Validation(
        report_id=report.id,
        expert_id=current_user.id,
        decision=body.decision,
        comment=body.comment,
        proposed_solution=body.proposed_solution,
        urgency_opinion=body.urgency_opinion,
    )
    db.add(validation)
    db.flush()

    old_status = report.status
    new_status = _DECISION_TO_STATUS[body.decision]
    report.status = new_status
    db.flush()

    write_audit_log(
        db,
        actor_id=current_user.id,
        action=AuditAction.STATUS_CHANGE,
        entity_type="report",
        entity_id=report.id,
        old_value={"status": old_status.value},
        new_value={"status": new_status.value},
    )

    douar = db.get(Douar, report.douar_id)
    notif_params = {"douar": douar.name_fr}
    if new_status == ReportStatus.RECHECK_REQUESTED:
        notify_user(
            db,
            user_id=report.moqaddem_id,
            type=NotificationType.RECHECK_REQUESTED,
            params=notif_params,
            entity_type="report",
            entity_id=report.id,
        )
    elif new_status == ReportStatus.VALIDATED:
        notify_user(
            db,
            user_id=report.moqaddem_id,
            type=NotificationType.VALIDATED,
            params=notif_params,
            entity_type="report",
            entity_id=report.id,
        )
        notify_all_managers(
            db,
            type=NotificationType.VALIDATED,
            params=notif_params,
            entity_type="report",
            entity_id=report.id,
        )
    # REJECTED: no notification trigger is listed for it in section 5 — ruling, see PROGRESS.md

    config = get_active_scoring_config(db, lang)
    recompute_priority(db, report, config)

    db.commit()
    db.refresh(validation)
    return ValidationCreateOut(
        id=validation.id,
        report_id=validation.report_id,
        expert_id=validation.expert_id,
        decision=validation.decision,
        comment=validation.comment,
        proposed_solution=validation.proposed_solution,
        urgency_opinion=validation.urgency_opinion,
        created_at=validation.created_at,
        new_report_status=new_status,
    )
