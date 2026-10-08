"""Import every model module so Base.metadata is complete for Alembic
autogenerate and for Base.metadata.create_all() in tests."""

from app.models.audit_log import AuditLog
from app.models.device_token import DeviceToken
from app.models.douar import Douar
from app.models.notification import Notification
from app.models.priority import Priority
from app.models.project import Project
from app.models.project_update import ProjectMedia, ProjectUpdate
from app.models.refresh_token import RefreshToken
from app.models.report import Report
from app.models.report_media import ReportMedia
from app.models.scoring_config import ScoringConfig
from app.models.territory import Territory, UserTerritory
from app.models.user import User
from app.models.validation import Validation

__all__ = [
    "AuditLog",
    "DeviceToken",
    "Douar",
    "Notification",
    "Priority",
    "Project",
    "ProjectMedia",
    "ProjectUpdate",
    "RefreshToken",
    "Report",
    "ReportMedia",
    "ScoringConfig",
    "Territory",
    "UserTerritory",
    "User",
    "Validation",
]
