import uuid

from geoalchemy2 import Geography
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin


class Douar(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "douars"

    name_ar: Mapped[str] = mapped_column(String(200), nullable=False)
    name_fr: Mapped[str] = mapped_column(String(200), nullable=False)
    commune_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("territories.id"), nullable=False
    )
    # Added by a later migration once PostGIS is available — see
    # alembic/versions and PROGRESS.md. nullable so the base schema can be
    # created without the extension.
    location = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    population: Mapped[int | None] = mapped_column(Integer, nullable=True)
    families_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
