import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PermissionRead(BaseModel):
    id: uuid.UUID
    code: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RoleRead(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    permissions: list[PermissionRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class UserRead(BaseModel):
    id: uuid.UUID
    username: str
    email: EmailStr
    is_active: bool
    roles: list[RoleRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class BootstrapAdminRequest(UserCreate):
    bootstrap_key: str = Field(..., min_length=16)
    role_name: str = Field(default="super_admin", min_length=3, max_length=50)
    seed_rbac: bool = True


class RBACSeedSummary(BaseModel):
    permissions_created: int
    roles_created: int
    role_permission_links_added: int


class BootstrapAdminResponse(BaseModel):
    user: UserRead
    rbac_seed: RBACSeedSummary


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str
