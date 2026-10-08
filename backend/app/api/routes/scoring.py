from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_request_language, require_roles
from app.db.session import get_db
from app.models.enums import AuditAction, UserRole
from app.models.scoring_config import ScoringConfig
from app.models.user import User
from app.schemas.scoring import RecomputeResultOut, ScoringConfigOut, ScoringConfigUpdate
from app.services.audit import write_audit_log
from app.services.priority import get_active_scoring_config, recompute_all_open_reports

router = APIRouter(prefix="/scoring-config", tags=["scoring"])

_require_read = require_roles(*list(UserRole))
_require_write = require_roles(UserRole.MANAGER)


@router.get("", response_model=ScoringConfigOut)
def get_scoring_config(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_read),
) -> ScoringConfig:
    return get_active_scoring_config(db, get_request_language(request))


@router.put("", response_model=RecomputeResultOut)
def update_scoring_config(
    body: ScoringConfigUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_write),
) -> RecomputeResultOut:
    lang = get_request_language(request)
    old_config = get_active_scoring_config(db, lang)
    old_config.is_active = False

    new_config = ScoringConfig(weights=body.weights, is_active=True, created_by=current_user.id)
    db.add(new_config)
    db.flush()

    reports_recomputed = recompute_all_open_reports(db, new_config)

    write_audit_log(
        db,
        actor_id=current_user.id,
        action=AuditAction.UPDATE,
        entity_type="scoring_config",
        entity_id=new_config.id,
        old_value={"weights": old_config.weights},
        new_value={"weights": new_config.weights},
    )
    db.commit()
    db.refresh(new_config)
    return RecomputeResultOut(
        config=ScoringConfigOut.model_validate(new_config),
        reports_recomputed=reports_recomputed,
    )
