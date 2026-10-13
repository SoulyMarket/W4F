import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import NotificationType


class NotificationOut(BaseModel):
    id: uuid.UUID
    type: NotificationType
    params: dict
    entity_type: str
    entity_id: uuid.UUID
    is_read: bool
    created_at: datetime
    message: str  # type/params rendered via app.i18n in the caller's language

    model_config = {"from_attributes": True}


class NotificationListOut(BaseModel):
    items: list[NotificationOut]
    total: int
    unread_count: int
    page: int
    page_size: int


class DeviceTokenCreate(BaseModel):
    fcm_token: str = Field(min_length=1, max_length=300)
    platform: str = Field(min_length=1, max_length=20)
