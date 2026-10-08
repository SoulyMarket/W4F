"""Enums backing the Postgres enum types used across section 4's data model.

Values are machine codes (English, lowercase, snake_case) — never UI text.
Clients/UI translate codes via app.i18n at the edge.

Each Postgres enum TYPE is instantiated exactly once below (as a SQLAlchemy
Enum) and imported by every model that uses it. Declaring `Enum(X, name=...)`
separately in two model files for the same type name is a common trap: within
one MetaData, SQLAlchemy does not reliably dedupe those into a single
CREATE TYPE, so a shared instance is used everywhere instead (e.g.
`severity_level` is used by both `reports.severity_reported` and
`validations.urgency_opinion`).
"""

from enum import StrEnum

from sqlalchemy import Enum as SAEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    MANAGER = "manager"
    EXPERT = "expert"
    MOQADDEM = "moqaddem"


class Language(StrEnum):
    AR = "ar"
    FR = "fr"


class TerritoryLevel(StrEnum):
    PROVINCE = "province"
    COMMUNE = "commune"


class WaterSource(StrEnum):
    NETWORK = "network"
    WELL = "well"
    SPRING = "spring"
    TANK_TRUCK = "tank_truck"
    RIVER = "river"
    OTHER = "other"


class ProblemType(StrEnum):
    NO_WATER = "no_water"
    INTERMITTENT = "intermittent"
    LOW_PRESSURE = "low_pressure"
    CONTAMINATION = "contamination"
    BROKEN_PUMP = "broken_pump"
    BROKEN_PIPE = "broken_pipe"
    DRY_SOURCE = "dry_source"
    OTHER = "other"


class InterruptionFrequency(StrEnum):
    PERMANENT = "permanent"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    RARE = "rare"


class SeverityLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReportStatus(StrEnum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    RECHECK_REQUESTED = "recheck_requested"
    VALIDATED = "validated"
    REJECTED = "rejected"
    CONVERTED_TO_PROJECT = "converted_to_project"


class MediaKind(StrEnum):
    PHOTO = "photo"
    VIDEO = "video"


class UploadStatus(StrEnum):
    PENDING = "pending"
    UPLOADED = "uploaded"


class ValidationDecision(StrEnum):
    VALIDATED = "validated"
    RECHECK_REQUESTED = "recheck_requested"
    MODIFIED = "modified"
    REJECTED = "rejected"


class SolutionType(StrEnum):
    PIPE_REPAIR = "pipe_repair"
    PUMP_REPAIR = "pump_repair"
    NETWORK_EXTENSION = "network_extension"
    RESERVOIR = "reservoir"
    SOURCE_IMPROVEMENT = "source_improvement"
    EQUIPMENT = "equipment"
    TEMPORARY_SOLUTION = "temporary_solution"
    TECHNICAL_STUDY = "technical_study"


class ProjectStatus(StrEnum):
    NEW = "new"
    IN_STUDY = "in_study"
    APPROVED = "approved"
    IN_PREPARATION = "in_preparation"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AuditAction(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    STATUS_CHANGE = "status_change"
    EXPORT = "export"


class NotificationType(StrEnum):
    NEW_REPORT = "new_report"
    RECHECK_REQUESTED = "recheck_requested"
    VALIDATED = "validated"
    PRIORITY_CHANGED = "priority_changed"
    PROJECT_CREATED = "project_created"
    PROJECT_STATUS_CHANGED = "project_status_changed"
    PROJECT_COMPLETED = "project_completed"


def _values(enum_cls):
    """StrEnum member *values* (lowercase codes) as the Postgres enum labels —
    not member *names* (SAEnum's default), which would create labels like
    'AR'/'FR' instead of 'ar'/'fr' and break every server_default/comparison
    that uses the lowercase code."""
    return [member.value for member in enum_cls]


USER_ROLE_ENUM = SAEnum(UserRole, name="user_role", native_enum=True, values_callable=_values)
LANGUAGE_ENUM = SAEnum(Language, name="language", native_enum=True, values_callable=_values)
TERRITORY_LEVEL_ENUM = SAEnum(
    TerritoryLevel, name="territory_level", native_enum=True, values_callable=_values
)
WATER_SOURCE_ENUM = SAEnum(
    WaterSource, name="water_source", native_enum=True, values_callable=_values
)
PROBLEM_TYPE_ENUM = SAEnum(
    ProblemType, name="problem_type", native_enum=True, values_callable=_values
)
INTERRUPTION_FREQUENCY_ENUM = SAEnum(
    InterruptionFrequency,
    name="interruption_frequency",
    native_enum=True,
    values_callable=_values,
)
SEVERITY_LEVEL_ENUM = SAEnum(
    SeverityLevel, name="severity_level", native_enum=True, values_callable=_values
)
REPORT_STATUS_ENUM = SAEnum(
    ReportStatus, name="report_status", native_enum=True, values_callable=_values
)
MEDIA_KIND_ENUM = SAEnum(MediaKind, name="media_kind", native_enum=True, values_callable=_values)
UPLOAD_STATUS_ENUM = SAEnum(
    UploadStatus, name="upload_status", native_enum=True, values_callable=_values
)
VALIDATION_DECISION_ENUM = SAEnum(
    ValidationDecision, name="validation_decision", native_enum=True, values_callable=_values
)
SOLUTION_TYPE_ENUM = SAEnum(
    SolutionType, name="solution_type", native_enum=True, values_callable=_values
)
PROJECT_STATUS_ENUM = SAEnum(
    ProjectStatus, name="project_status", native_enum=True, values_callable=_values
)
AUDIT_ACTION_ENUM = SAEnum(
    AuditAction, name="audit_action", native_enum=True, values_callable=_values
)
NOTIFICATION_TYPE_ENUM = SAEnum(
    NotificationType, name="notification_type", native_enum=True, values_callable=_values
)


# Allowed project status transitions (section 5). Any non-terminal status
# may also move to `cancelled`.
PROJECT_STATUS_TRANSITIONS: dict[ProjectStatus, set[ProjectStatus]] = {
    ProjectStatus.NEW: {ProjectStatus.IN_STUDY, ProjectStatus.CANCELLED},
    ProjectStatus.IN_STUDY: {ProjectStatus.APPROVED, ProjectStatus.CANCELLED},
    ProjectStatus.APPROVED: {ProjectStatus.IN_PREPARATION, ProjectStatus.CANCELLED},
    ProjectStatus.IN_PREPARATION: {ProjectStatus.IN_PROGRESS, ProjectStatus.CANCELLED},
    ProjectStatus.IN_PROGRESS: {ProjectStatus.COMPLETED, ProjectStatus.CANCELLED},
    ProjectStatus.COMPLETED: set(),
    ProjectStatus.CANCELLED: set(),
}
