import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import TERRITORY_LEVEL_ENUM, TerritoryLevel
from app.models.mixins import TimestampMixin, UUIDPKMixin


class Territory(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "territories"

    name_ar: Mapped[str] = mapped_column(String(200), nullable=False)
    name_fr: Mapped[str] = mapped_column(String(200), nullable=False)
    level: Mapped[TerritoryLevel] = mapped_column(TERRITORY_LEVEL_ENUM, nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("territories.id"), nullable=True
    )


class UserTerritory(Base):
    __tablename__ = "user_territories"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    territory_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("territories.id", ondelete="CASCADE"), primary_key=True
    )
