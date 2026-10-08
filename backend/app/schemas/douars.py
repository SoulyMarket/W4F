import uuid

from pydantic import BaseModel, Field


class DouarCreate(BaseModel):
    name_ar: str = Field(min_length=1, max_length=200)
    name_fr: str = Field(min_length=1, max_length=200)
    commune_id: uuid.UUID
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    population: int | None = Field(default=None, ge=0)
    families_count: int | None = Field(default=None, ge=0)
    notes: str | None = None


class DouarUpdate(BaseModel):
    name_ar: str | None = Field(default=None, min_length=1, max_length=200)
    name_fr: str | None = Field(default=None, min_length=1, max_length=200)
    lat: float | None = Field(default=None, ge=-90, le=90)
    lon: float | None = Field(default=None, ge=-180, le=180)
    population: int | None = Field(default=None, ge=0)
    families_count: int | None = Field(default=None, ge=0)
    notes: str | None = None


class DouarOut(BaseModel):
    id: uuid.UUID
    name_ar: str
    name_fr: str
    commune_id: uuid.UUID
    lat: float | None
    lon: float | None
    population: int | None
    families_count: int | None
    notes: str | None


class DouarListOut(BaseModel):
    items: list[DouarOut]
    total: int
    page: int
    page_size: int
