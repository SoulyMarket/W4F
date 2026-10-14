"""Sync API (section 9 step 2.1) — the moqaddem phone's only way to create
reports. There's deliberately no `POST /reports`: `reports.id` is
client-generated specifically so this endpoint can be idempotent (section
4), and `GET /reports`/`GET /reports/{id}` (reports.py) stay read-only.
"""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_request_language, get_settings, require_roles
from app.api.routes.reports import latest_priority_subquery, report_to_out
from app.core.config import Settings
from app.core.geo import latlon_from_point, point_from_latlon
from app.db.session import get_db
from app.i18n import t
from app.models.douar import Douar
from app.models.enums import NotificationType, ReportStatus, UploadStatus, UserRole
from app.models.notification import Notification
from app.models.priority import Priority
from app.models.project import Project
from app.models.project_update import ProjectUpdate
from app.models.report import Report
from app.models.report_media import ReportMedia
from app.models.user import User
from app.models.validation import Validation
from app.schemas.notifications import NotificationOut
from app.schemas.sync import (
    SyncDouarOut,
    SyncMediaPush,
    SyncMediaResultOut,
    SyncPriorityOut,
    SyncProjectOut,
    SyncProjectUpdateOut,
    SyncPullOut,
    SyncPushOut,
    SyncPushRequest,
    SyncReportPush,
    SyncReportResultOut,
    SyncValidationOut,
)
from app.services.notifications import notify_territory_experts
from app.services.priority import get_active_scoring_config, recompute_priority
from app.services.storage import UPLOAD_URL_EXPIRE_SECONDS, generate_upload_url, get_s3_client
from app.services.territory_scope import get_accessible_territory_ids

router = APIRouter(prefix="/sync", tags=["sync"])

_require_moqaddem = require_roles(UserRole.MOQADDEM)

_EXTENSION_BY_MIME = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "video/mp4": ".mp4",
}

# Fields the field agent can set/edit directly. moqaddem_id/status/version/
# synced_at are server-controlled, never taken from the client payload.
_MUTABLE_FIELDS = (
    "water_source",
    "problem_type",
    "problem_started_on",
    "duration_days",
    "interruption_frequency",
    "has_alternative_source",
    "severity_reported",
    "water_quality_risk",
    "affected_families",
    "affected_people",
    "observations",
)


def _report_unchanged(report: Report, item: SyncReportPush) -> bool:
    if any(getattr(report, field) != getattr(item, field) for field in _MUTABLE_FIELDS):
        return False
    existing_distance = (
        float(report.alternative_distance_km)
        if report.alternative_distance_km is not None
        else None
    )
    if existing_distance != item.alternative_distance_km:
        return False
    existing_coords = latlon_from_point(report.location)
    incoming_coords = (
        (item.lat, item.lon) if item.lat is not None and item.lon is not None else None
    )
    return existing_coords == incoming_coords


def _apply_report_fields(report: Report, item: SyncReportPush) -> None:
    for field in _MUTABLE_FIELDS:
        setattr(report, field, getattr(item, field))
    report.alternative_distance_km = item.alternative_distance_km
    report.location_accuracy_m = item.location_accuracy_m
    if item.lat is not None and item.lon is not None:
        report.location = point_from_latlon(item.lat, item.lon)


def _register_media(
    db: Session, settings: Settings, report: Report, media_items: list[SyncMediaPush]
) -> list[SyncMediaResultOut]:
    """Idempotent per media item, keyed on the natural (report, kind, mime,
    size, captured_at) tuple rather than a client-generated id — a WorkManager
    retry of the exact same push resends the exact same captured_at, so this
    still dedupes correctly without needing a schema change to
    `report_media.id`. Pre-registers each new item and hands back a presigned
    PUT URL immediately (the same one `/media/upload-url` would give, just
    batched here since the client is already batching everything else)."""
    results = []
    client = get_s3_client(settings)
    for m in media_items:
        existing = (
            db.query(ReportMedia)
            .filter_by(
                report_id=report.id,
                kind=m.kind,
                mime_type=m.mime_type,
                size_bytes=m.size_bytes,
                captured_at=m.captured_at,
            )
            .first()
        )
        if existing is not None:
            results.append(
                SyncMediaResultOut(
                    media_id=existing.id,
                    kind=existing.kind,
                    mime_type=existing.mime_type,
                    already_uploaded=existing.upload_status == UploadStatus.UPLOADED,
                )
            )
            continue

        extension = _EXTENSION_BY_MIME.get(m.mime_type, "")
        object_key = f"reports/{report.id}/{uuid.uuid4()}{extension}"
        media = ReportMedia(
            report_id=report.id,
            kind=m.kind,
            object_key=object_key,
            mime_type=m.mime_type,
            size_bytes=m.size_bytes,
            captured_at=m.captured_at,
            upload_status=UploadStatus.PENDING,
        )
        db.add(media)
        db.flush()
        upload_url = generate_upload_url(client, settings.minio_bucket, object_key, m.mime_type)
        results.append(
            SyncMediaResultOut(
                media_id=media.id,
                kind=media.kind,
                mime_type=media.mime_type,
                already_uploaded=False,
                upload_url=upload_url,
                object_key=object_key,
                expires_in=UPLOAD_URL_EXPIRE_SECONDS,
            )
        )
    return results


@router.post("/push", response_model=SyncPushOut)
def push(
    body: SyncPushRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_moqaddem),
    settings: Settings = Depends(get_settings),
) -> SyncPushOut:
    lang = get_request_language(request)
    accessible = get_accessible_territory_ids(db, current_user)
    config = get_active_scoring_config(db, lang)
    results: list[SyncReportResultOut] = []

    for item in body.reports:
        douar = db.get(Douar, item.douar_id)
        if douar is None or douar.commune_id not in accessible:
            results.append(
                SyncReportResultOut(id=item.id, status="rejected", error="errors.not_found")
            )
            continue

        report = db.get(Report, item.id)

        if report is None:
            report = Report(
                id=item.id,
                douar_id=item.douar_id,
                moqaddem_id=current_user.id,
                water_source=item.water_source,
                problem_type=item.problem_type,
                problem_started_on=item.problem_started_on,
                duration_days=item.duration_days,
                interruption_frequency=item.interruption_frequency,
                has_alternative_source=item.has_alternative_source,
                alternative_distance_km=item.alternative_distance_km,
                severity_reported=item.severity_reported,
                water_quality_risk=item.water_quality_risk,
                affected_families=item.affected_families,
                affected_people=item.affected_people,
                observations=item.observations,
                location=(
                    point_from_latlon(item.lat, item.lon)
                    if item.lat is not None and item.lon is not None
                    else None
                ),
                location_accuracy_m=item.location_accuracy_m,
                collected_at=item.collected_at,
                synced_at=datetime.now(UTC),
            )
            db.add(report)
            db.flush()
            media_results = _register_media(db, settings, report, item.media)
            recompute_priority(db, report, config)
            notify_territory_experts(
                db,
                territory_id=douar.commune_id,
                type=NotificationType.NEW_REPORT,
                params={"douar": douar.name_fr},
                entity_type="report",
                entity_id=report.id,
            )
            results.append(
                SyncReportResultOut(
                    id=report.id, status="created", version=report.version, media=media_results
                )
            )
            continue

        if report.moqaddem_id != current_user.id:
            # Hide existence of another moqaddem's report — same
            # 404-not-403 convention as cross-territory access elsewhere.
            results.append(
                SyncReportResultOut(id=item.id, status="rejected", error="errors.not_found")
            )
            continue

        if report.status != ReportStatus.SUBMITTED:
            # Conflict rule (section 5): server wins once review has moved
            # the report past `submitted` — field-data edits are rejected,
            # the moqaddem must create a new observation instead.
            results.append(
                SyncReportResultOut(
                    id=report.id,
                    status="rejected",
                    error="errors.sync_conflict",
                    version=report.version,
                )
            )
            continue

        if _report_unchanged(report, item):
            media_results = _register_media(db, settings, report, item.media)
            results.append(
                SyncReportResultOut(
                    id=report.id, status="unchanged", version=report.version, media=media_results
                )
            )
            continue

        _apply_report_fields(report, item)
        report.version += 1
        report.synced_at = datetime.now(UTC)
        db.flush()
        media_results = _register_media(db, settings, report, item.media)
        recompute_priority(db, report, config)
        results.append(
            SyncReportResultOut(
                id=report.id, status="updated", version=report.version, media=media_results
            )
        )

    db.commit()
    return SyncPushOut(results=results)


def _notification_to_out(notification: Notification, lang: str) -> NotificationOut:
    message = t(f"notifications.{notification.type.value}", lang, **notification.params)
    return NotificationOut(
        id=notification.id,
        type=notification.type,
        params=notification.params,
        entity_type=notification.entity_type,
        entity_id=notification.entity_id,
        is_read=notification.is_read,
        created_at=notification.created_at,
        message=message,
    )


@router.get("/pull", response_model=SyncPullOut)
def pull(
    request: Request,
    since: datetime | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_moqaddem),
) -> SyncPullOut:
    """Everything in the moqaddem's territory that changed since `since`
    (omit for a first/full pull): reference data (douars) plus everything
    about their own reports (statuses, priorities, validations, projects,
    updates) and their own notifications. `cursor` is captured before any
    query runs, so a row written mid-pull is simply re-delivered on the
    next pull rather than silently missed — redelivery is harmless for a
    read-only sync target, a gap is not."""
    lang = get_request_language(request)
    cursor = datetime.now(UTC)
    accessible = get_accessible_territory_ids(db, current_user)

    douars_query = db.query(Douar).filter(Douar.commune_id.in_(accessible))
    if since is not None:
        douars_query = douars_query.filter(Douar.updated_at > since)
    douars_out = []
    for d in douars_query.all():
        coords = latlon_from_point(d.location)
        douars_out.append(
            SyncDouarOut(
                id=d.id,
                name_ar=d.name_ar,
                name_fr=d.name_fr,
                commune_id=d.commune_id,
                lat=coords[0] if coords else None,
                lon=coords[1] if coords else None,
                population=d.population,
                families_count=d.families_count,
            )
        )

    reports_query = db.query(Report).filter(Report.moqaddem_id == current_user.id)
    if since is not None:
        reports_query = reports_query.filter(Report.updated_at > since)
    reports = reports_query.all()

    latest = latest_priority_subquery(db)
    score_by_report = dict(
        db.query(Report.id, Priority.score)
        .outerjoin(latest, latest.c.report_id == Report.id)
        .outerjoin(
            Priority,
            (Priority.report_id == latest.c.report_id)
            & (Priority.computed_at == latest.c.computed_at),
        )
        .filter(Report.id.in_([r.id for r in reports]))
        .all()
        if reports
        else []
    )
    reports_out = [report_to_out(r, score_by_report.get(r.id)) for r in reports]

    priorities_query = (
        db.query(Priority)
        .join(Report, Priority.report_id == Report.id)
        .filter(Report.moqaddem_id == current_user.id)
    )
    if since is not None:
        priorities_query = priorities_query.filter(Priority.computed_at > since)
    priorities_out = [
        SyncPriorityOut(report_id=p.report_id, score=p.score, computed_at=p.computed_at)
        for p in priorities_query.all()
    ]

    validations_query = (
        db.query(Validation)
        .join(Report, Validation.report_id == Report.id)
        .filter(Report.moqaddem_id == current_user.id)
    )
    if since is not None:
        validations_query = validations_query.filter(Validation.created_at > since)
    validations_out = [
        SyncValidationOut(
            id=v.id,
            report_id=v.report_id,
            expert_id=v.expert_id,
            decision=v.decision,
            comment=v.comment,
            proposed_solution=v.proposed_solution,
            urgency_opinion=v.urgency_opinion,
            created_at=v.created_at,
        )
        for v in validations_query.all()
    ]

    projects_query = (
        db.query(Project)
        .join(Report, Project.report_id == Report.id)
        .filter(Report.moqaddem_id == current_user.id)
    )
    if since is not None:
        projects_query = projects_query.filter(Project.updated_at > since)
    projects = projects_query.all()
    projects_out = [
        SyncProjectOut(
            id=p.id,
            report_id=p.report_id,
            title=p.title,
            solution_type=p.solution_type,
            status=p.status,
            progress_percent=p.progress_percent,
            planned_start=p.planned_start,
            planned_end=p.planned_end,
            actual_start=p.actual_start,
            actual_end=p.actual_end,
        )
        for p in projects
    ]

    project_updates_query = (
        db.query(ProjectUpdate)
        .join(Project, ProjectUpdate.project_id == Project.id)
        .join(Report, Project.report_id == Report.id)
        .filter(Report.moqaddem_id == current_user.id)
    )
    if since is not None:
        project_updates_query = project_updates_query.filter(ProjectUpdate.created_at > since)
    project_updates_out = [
        SyncProjectUpdateOut(
            id=u.id,
            project_id=u.project_id,
            old_status=u.old_status,
            new_status=u.new_status,
            progress_percent=u.progress_percent,
            note=u.note,
            created_at=u.created_at,
        )
        for u in project_updates_query.all()
    ]

    notifications_query = db.query(Notification).filter_by(user_id=current_user.id)
    if since is not None:
        notifications_query = notifications_query.filter(Notification.created_at > since)
    notifications_out = [_notification_to_out(n, lang) for n in notifications_query.all()]

    return SyncPullOut(
        cursor=cursor,
        douars=douars_out,
        reports=reports_out,
        priorities=priorities_out,
        validations=validations_out,
        projects=projects_out,
        project_updates=project_updates_out,
        notifications=notifications_out,
    )
