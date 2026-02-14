from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import hash_password
from app.models import Permission, Role, User

PERMISSION_CATALOG: dict[str, list[str]] = {
    "products": ["create", "read", "update", "delete"],
    "inventory": ["create", "read", "update", "delete", "adjust"],
    "purchasing": ["create", "read", "update", "delete", "approve"],
    "sales": ["create", "read", "update", "delete", "approve"],
    "production": ["create", "read", "update", "delete", "release"],
    "users": ["create", "read", "update", "delete", "assign_roles"],
    "roles": ["create", "read", "update", "delete", "assign_permissions"],
}

ROLE_PERMISSION_MAP: dict[str, set[str]] = {
    "super_admin": {f"{module}:{action}" for module, actions in PERMISSION_CATALOG.items() for action in actions},
    "admin": {f"{module}:{action}" for module, actions in PERMISSION_CATALOG.items() for action in actions if not (module == "users" and action == "delete")},
    "manager": {
        "products:create",
        "products:read",
        "products:update",
        "inventory:read",
        "inventory:adjust",
        "purchasing:create",
        "purchasing:read",
        "purchasing:update",
        "purchasing:approve",
        "sales:create",
        "sales:read",
        "sales:update",
        "sales:approve",
        "production:create",
        "production:read",
        "production:update",
        "production:release",
        "users:read",
        "roles:read",
    },
    "viewer": {f"{module}:read" for module in PERMISSION_CATALOG},
}

ROLE_DESCRIPTIONS: dict[str, str] = {
    "super_admin": "Full platform access including security and user administration",
    "admin": "Operational administration without destructive user deletion",
    "manager": "Department manager access for day-to-day ERP operations",
    "viewer": "Read-only access across ERP modules",
}


class BootstrapError(Exception):
    pass


def _all_permission_codes() -> list[str]:
    return [f"{module}:{action}" for module, actions in PERMISSION_CATALOG.items() for action in actions]


async def seed_rbac(db: AsyncSession) -> dict[str, int]:
    summary = {
        "permissions_created": 0,
        "roles_created": 0,
        "role_permission_links_added": 0,
    }

    all_codes = _all_permission_codes()

    existing_permissions = {permission.code: permission for permission in (await db.scalars(select(Permission).where(Permission.code.in_(all_codes)))).all()}

    for code in all_codes:
        if code not in existing_permissions:
            module, action = code.split(":", 1)
            permission = Permission(
                code=code,
                description=f"Can {action} in {module} module",
            )
            db.add(permission)
            existing_permissions[code] = permission
            summary["permissions_created"] += 1

    await db.flush()

    roles = {role.name: role for role in (await db.scalars(select(Role).options(selectinload(Role.permissions)))).all()}

    for role_name, permission_codes in ROLE_PERMISSION_MAP.items():
        role = roles.get(role_name)
        if role is None:
            role = Role(
                name=role_name,
                description=ROLE_DESCRIPTIONS.get(role_name),
            )
            db.add(role)
            roles[role_name] = role
            summary["roles_created"] += 1

    await db.flush()

    # Load roles with permissions to avoid lazy loading issues
    result = await db.execute(select(Role).options(selectinload(Role.permissions)))
    loaded_roles = {role.name: role for role in result.scalars()}

    for role_name, permission_codes in ROLE_PERMISSION_MAP.items():
        role = loaded_roles[role_name]
        current_codes = {permission.code for permission in role.permissions}
        missing_codes = permission_codes - current_codes

        for code in sorted(missing_codes):
            role.permissions.append(existing_permissions[code])
            summary["role_permission_links_added"] += 1

    await db.commit()
    return summary


async def bootstrap_admin_user(
    db: AsyncSession,
    *,
    username: str,
    email: str,
    password: str,
    role_name: str = "super_admin",
) -> User:
    if len(password) < 8:
        raise BootstrapError("Password must be at least 8 characters")

    role = await db.scalar(select(Role).options(selectinload(Role.permissions)).where(Role.name == role_name))
    if role is None:
        raise BootstrapError(f"Role '{role_name}' not found. Run RBAC seed first or use --seed-rbac.")

    existing = await db.scalar(select(User).where(or_(User.username == username, User.email == email)))
    if existing:
        raise BootstrapError("Username or email already exists")

    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
        is_active=True,
        roles=[role],
    )
    db.add(user)
    await db.commit()

    created_user = await db.scalar(select(User).options(selectinload(User.roles).selectinload(Role.permissions)).where(User.id == user.id))
    if created_user is None:
        raise BootstrapError("Failed to create bootstrap admin user")

    return created_user
