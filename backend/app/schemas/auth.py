import uuid

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.enums import Language, UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        return v.lower()


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=10)


class TerritorySummary(BaseModel):
    id: uuid.UUID
    name_ar: str
    name_fr: str
    level: str

    model_config = {"from_attributes": True}


class MeResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str
    role: UserRole
    preferred_language: Language
    territories: list[TerritorySummary]

    model_config = {"from_attributes": True}
