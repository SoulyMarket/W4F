import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.enums import Language, UserRole


class UserCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    phone: str | None = None
    password: str = Field(min_length=10)
    role: UserRole
    preferred_language: Language = Language.AR

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        return v.lower()


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    email: EmailStr | None = None
    phone: str | None = None
    role: UserRole | None = None
    preferred_language: Language | None = None

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, v: str | None) -> str | None:
        return v.lower() if v else v


class UserOut(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str
    phone: str | None
    role: UserRole
    preferred_language: Language
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserListOut(BaseModel):
    items: list[UserOut]
    total: int
    page: int
    page_size: int


class ResetPasswordResponse(BaseModel):
    temporary_password: str


class UserTerritoriesUpdate(BaseModel):
    territory_ids: list[uuid.UUID]
