"""Authentication and user schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import EmailStr, Field, field_validator

from app.schemas.common import BaseSchema, TimestampSchema


# ---- Auth Schemas ----

class LoginRequest(BaseSchema):
    """Login request with username/email and password."""

    username: str = Field(min_length=1, max_length=255, description="Username or email")
    password: str = Field(min_length=8, max_length=128, description="Password")


class RegisterRequest(BaseSchema):
    """New user registration request."""

    username: str = Field(min_length=3, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Ensure password meets minimum complexity requirements."""
        if len(v) < 8:
            msg = "Password must be at least 8 characters"
            raise ValueError(msg)
        if not any(c.isupper() for c in v):
            msg = "Password must contain at least one uppercase letter"
            raise ValueError(msg)
        if not any(c.islower() for c in v):
            msg = "Password must contain at least one lowercase letter"
            raise ValueError(msg)
        if not any(c.isdigit() for c in v):
            msg = "Password must contain at least one digit"
            raise ValueError(msg)
        return v


class TokenResponse(BaseSchema):
    """JWT token pair response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token expiry in seconds")


class RefreshTokenRequest(BaseSchema):
    """Token refresh request."""

    refresh_token: str


# ---- User Schemas ----

class UserCreate(BaseSchema):
    """Admin user creation schema."""

    username: str = Field(min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = None
    is_active: bool = True
    is_superuser: bool = False
    role_ids: list[str] = Field(default_factory=list)


class UserUpdate(BaseSchema):
    """User profile update schema."""

    full_name: str | None = None
    email: EmailStr | None = None
    avatar_url: str | None = None
    preferences: str | None = None


class UserAdminUpdate(BaseSchema):
    """Admin user update schema — allows modifying active/superuser status."""

    full_name: str | None = None
    email: EmailStr | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None
    role_ids: list[str] | None = None


class PasswordChangeRequest(BaseSchema):
    """Password change request."""

    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class UserResponse(TimestampSchema):
    """User response schema (excludes sensitive fields)."""

    id: str
    username: str
    email: str
    full_name: str | None = None
    avatar_url: str | None = None
    is_active: bool
    is_superuser: bool
    last_login: datetime | None = None
    roles: list[RoleResponse] = Field(default_factory=list)


class UserBriefResponse(BaseSchema):
    """Compact user reference for embedding in other responses."""

    id: str
    username: str
    full_name: str | None = None
    avatar_url: str | None = None


class RoleResponse(BaseSchema):
    """Role response schema."""

    id: str
    name: str
    description: str | None = None
    is_system: bool = False
    permissions: list[PermissionResponse] = Field(default_factory=list)


class PermissionResponse(BaseSchema):
    """Permission response schema."""

    id: str
    name: str
    resource: str
    action: str
    description: str | None = None


# Forward reference update
UserResponse.model_rebuild()
