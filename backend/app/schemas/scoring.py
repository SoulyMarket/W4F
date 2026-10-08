import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator

from app.services.scoring import DEFAULT_WEIGHTS

_REQUIRED_CRITERIA = set(DEFAULT_WEIGHTS)


class ScoringConfigOut(BaseModel):
    id: uuid.UUID
    weights: dict[str, float]
    is_active: bool
    created_by: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class ScoringConfigUpdate(BaseModel):
    weights: dict[str, float]

    @field_validator("weights")
    @classmethod
    def validate_weights(cls, v: dict[str, float]) -> dict[str, float]:
        missing = _REQUIRED_CRITERIA - v.keys()
        extra = v.keys() - _REQUIRED_CRITERIA
        if missing:
            raise ValueError(f"missing weight(s) for: {sorted(missing)}")
        if extra:
            raise ValueError(f"unknown weight criterion/criteria: {sorted(extra)}")
        for criterion, value in v.items():
            if not (0 <= value <= 100):
                raise ValueError(f"weight for {criterion!r} must be between 0 and 100")
        return v


class RecomputeResultOut(BaseModel):
    config: ScoringConfigOut
    reports_recomputed: int
