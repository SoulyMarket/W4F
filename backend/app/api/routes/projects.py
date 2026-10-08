import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_request_language, require_roles
from app.db.session import get_db
from app.i18n import t
from app.models.douar import Douar
from app.models.enums import (
    PROJECT_STATUS_TRANSITIONS,
    AuditAction,
    NotificationType,
    ProjectStatus,
    ReportStatus,
    UserRole,
)
from app.models.project import Project
from app.models.project_update import ProjectUpdate
from app.models.report import Report
from app.models.user import User
from app.schemas.projects import (
    ProjectCreate,
    ProjectDetailOut,
    ProjectListOut,
    ProjectOut,
    ProjectStatusChangeCreate,
    ProjectUpdateIn,
    ProjectUpdateOut,
)
from app.services.audit import write_audit_log
from app.services.notifications import notify_all_managers, notify_user
from app.services.territory_scope import territory_scope_filter

router = APIRouter(tags=["projects"])

_require_any = require_roles(*list(UserRole))
_require_manager = require_roles(UserRole.MANAGER)


def _projects_query_with_scope(db: Session, user: User):
    scope = territory_scope_filter(Douar.commune_id, db, user)
    return db.query(Project).join(Douar, Project.douar_id == Douar.id).filter(scope)


@router.post(
    "/reports/{report_id}/project", response_model=ProjectOut, status_code=status.HTTP_201_CREATED
)
def create_project_from_report(
    report_id: uuid.UUID,
    body: ProjectCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_manager),
) -> Project:
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
    if report.status != ReportStatus.VALIDATED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=t("errors.report_not_validated", lang),
        )

    project = Project(
        report_id=report.id,
        douar_id=report.douar_id,
        title=body.title,
        solution_type=body.solution_type,
        description=body.description,
        owner_id=body.owner_id or current_user.id,
        planned_start=body.planned_start,
        planned_end=body.planned_end,
    )
    db.add(project)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=t("errors.validation_error", lang),
        ) from None

    old_status = report.status
    report.status = ReportStatus.CONVERTED_TO_PROJECT
    db.flush()

    write_audit_log(
        db,
        actor_id=current_user.id,
        action=AuditAction.CREATE,
        entity_type="project",
        entity_id=project.id,
        new_value={"title": project.title, "report_id": str(report.id)},
    )
    write_audit_log(
        db,
        actor_id=current_user.id,
        action=AuditAction.STATUS_CHANGE,
        entity_type="report",
        entity_id=report.id,
        old_value={"status": old_status.value},
        new_value={"status": report.status.value},
    )

    douar = db.get(Douar, report.douar_id)
    notif_params = {"douar": douar.name_fr}
    notify_user(
        db,
        user_id=report.moqaddem_id,
        type=NotificationType.PROJECT_CREATED,
        params=notif_params,
        entity_type="project",
        entity_id=project.id,
    )
    notify_all_managers(
        db,
        type=NotificationType.PROJECT_CREATED,
        params=notif_params,
        entity_type="project",
        entity_id=project.id,
    )

    db.commit()
    db.refresh(project)
    return project


@router.get("/projects", response_model=ProjectListOut)
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_any),
    status_filter: ProjectStatus | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ProjectListOut:
    query = _projects_query_with_scope(db, current_user)
    if status_filter is not None:
        query = query.filter(Project.status == status_filter)

    total = query.with_entities(func.count(Project.id)).scalar()
    items = (
        query.order_by(Project.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return ProjectListOut(
        items=[ProjectOut.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
    )


def _get_project_or_404(db: Session, project_id: uuid.UUID, user: User, lang: str) -> Project:
    project = _projects_query_with_scope(db, user).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=t("errors.not_found", lang)
        )
    return project


@router.get("/projects/{project_id}", response_model=ProjectDetailOut)
def get_project(
    project_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_any),
) -> ProjectDetailOut:
    lang = get_request_language(request)
    project = _get_project_or_404(db, project_id, current_user, lang)
    updates = (
        db.query(ProjectUpdate)
        .filter_by(project_id=project.id)
        .order_by(ProjectUpdate.created_at.desc())
        .all()
    )
    return ProjectDetailOut(
        **ProjectOut.model_validate(project).model_dump(),
        updates=[ProjectUpdateOut.model_validate(u) for u in updates],
    )


@router.patch("/projects/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: uuid.UUID,
    body: ProjectUpdateIn,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_manager),
) -> Project:
    lang = get_request_language(request)
    project = _get_project_or_404(db, project_id, current_user, lang)

    old_value = {"title": project.title, "description": project.description}
    updates = body.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(project, field, value)
    db.flush()

    write_audit_log(
        db,
        actor_id=current_user.id,
        action=AuditAction.UPDATE,
        entity_type="project",
        entity_id=project.id,
        old_value=old_value,
        new_value={"title": project.title, "description": project.description},
    )
    db.commit()
    db.refresh(project)
    return project


@router.post(
    "/projects/{project_id}/updates",
    response_model=ProjectUpdateOut,
    status_code=status.HTTP_201_CREATED,
)
def add_project_update(
    project_id: uuid.UUID,
    body: ProjectStatusChangeCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_manager),
) -> ProjectUpdate:
    lang = get_request_language(request)
    project = _get_project_or_404(db, project_id, current_user, lang)

    old_status = project.status
    allowed = PROJECT_STATUS_TRANSITIONS.get(old_status, set())
    if body.new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=t("errors.invalid_status_transition", lang),
        )

    project.status = body.new_status
    if body.progress_percent is not None:
        project.progress_percent = body.progress_percent
    db.flush()

    update = ProjectUpdate(
        project_id=project.id,
        author_id=current_user.id,
        old_status=old_status,
        new_status=body.new_status,
        progress_percent=body.progress_percent,
        note=body.note,
    )
    db.add(update)

    write_audit_log(
        db,
        actor_id=current_user.id,
        action=AuditAction.STATUS_CHANGE,
        entity_type="project",
        entity_id=project.id,
        old_value={"status": old_status.value},
        new_value={"status": body.new_status.value},
    )

    report = db.get(Report, project.report_id)
    douar = db.get(Douar, project.douar_id)
    notif_type = (
        NotificationType.PROJECT_COMPLETED
        if body.new_status == ProjectStatus.COMPLETED
        else NotificationType.PROJECT_STATUS_CHANGED
    )
    notif_params = {"douar": douar.name_fr, "status": body.new_status.value}
    notify_user(
        db,
        user_id=report.moqaddem_id,
        type=notif_type,
        params=notif_params,
        entity_type="project",
        entity_id=project.id,
    )
    notify_all_managers(
        db, type=notif_type, params=notif_params, entity_type="project", entity_id=project.id
    )

    db.commit()
    db.refresh(update)
    return update
