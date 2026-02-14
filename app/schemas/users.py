"""Pydantic schemas for user management"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    username: str = Field(max_length=50)
    email: EmailStr
    full_name: str | None = None
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(min_length=8)


class UserUpdate(BaseModel):
    username: str | None = Field(None, max_length=50)
    email: EmailStr | None = None
    full_name: str | None = None
    is_active: bool | None = None


class User(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    last_login: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class PermissionBase(BaseModel):
    code: str = Field(max_length=100)
    description: str | None = None


class Permission(PermissionBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)


class RoleBase(BaseModel):
    name: str = Field(max_length=50)
    description: str | None = None


class RoleCreate(RoleBase):
    permission_ids: list[UUID] | None = None
    is_active: bool = True


class RoleUpdate(BaseModel):
    name: str | None = Field(None, max_length=50)
    description: str | None = None
    permission_ids: list[UUID] | None = None


class Role(RoleBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)


class UserRoleAssignment(BaseModel):
    user_id: UUID
    role_id: UUID


class UserProfile(BaseModel):
    id: UUID
    username: str
    email: str
    full_name: str | None
    is_active: bool
    created_at: datetime
    last_login: datetime | None
    roles: list[str]


class UserSummary(BaseModel):
    total_users: int
    active_users: int
    inactive_users: int
    total_roles: int
    total_permissions: int
