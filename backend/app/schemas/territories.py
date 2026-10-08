import uuid

from pydantic import BaseModel, Field

from app.models.enums import TerritoryLevel


class TerritoryCreate(BaseModel):
    name_ar: str = Field(min_length=1, max_length=200)
    name_fr: str = Field(min_length=1, max_length=200)
    level: TerritoryLevel
    parent_id: uuid.UUID | None = None


class TerritoryUpdate(BaseModel):
    name_ar: str | None = Field(default=None, min_length=1, max_length=200)
    name_fr: str | None = Field(default=None, min_length=1, max_length=200)
    parent_id: uuid.UUID | None = None


class TerritoryOut(BaseModel):
    id: uuid.UUID
    name_ar: str
    name_fr: str
    level: TerritoryLevel
    parent_id: uuid.UUID | None

    model_config = {"from_attributes": True}
