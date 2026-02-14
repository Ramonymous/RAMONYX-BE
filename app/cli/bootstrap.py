import argparse
import asyncio

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.database import SessionLocal
from app.models import Role, User
from app.services import BootstrapError, bootstrap_admin_user, seed_rbac
from app.services.sample_data_seeder import seed_sample_data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="erp-bootstrap",
        description="Seed RBAC data and bootstrap admin users for Ramonyxs ERP backend.",
    )
    parser.add_argument(
        "--seed-rbac",
        action="store_true",
        help="Create/update default permissions, roles, and role-permission links.",
    )
    parser.add_argument(
        "--seed-sample-data",
        action="store_true",
        help=(
            "Create interconnected sample data across all modules "
            "(suppliers, customers, products, orders, etc.)."
        ),
    )
    parser.add_argument(
        "--bootstrap-admin",
        action="store_true",
        help="Create an admin user and assign role (requires --username, --email, --password).",
    )
    parser.add_argument("--username", type=str, help="Admin username")
    parser.add_argument("--email", type=str, help="Admin email")
    parser.add_argument("--password", type=str, help="Admin password")
    parser.add_argument(
        "--role",
        type=str,
        default="super_admin",
        help="Role assigned to bootstrap admin (default: super_admin)",
    )
    parser.add_argument(
        "--allow-existing-users",
        action="store_true",
        help="Allow bootstrap admin creation even when users already exist.",
    )
    return parser


def _require_admin_args(args: argparse.Namespace) -> None:
    missing = [
        flag
        for flag, value in {
            "--username": args.username,
            "--email": args.email,
            "--password": args.password,
        }.items()
        if not value
    ]
    if missing:
        raise SystemExit(f"Missing required args for --bootstrap-admin: {', '.join(missing)}")


async def _run(args: argparse.Namespace) -> int:
    if not args.seed_rbac and not args.bootstrap_admin and not args.seed_sample_data:
        print("Nothing to do. Use --seed-rbac, --seed-sample-data, and/or --bootstrap-admin.")
        return 1

    async with SessionLocal() as db:
        if args.bootstrap_admin and not args.allow_existing_users:
            user_count = await db.scalar(select(func.count()).select_from(User))
            if user_count and user_count > 0:
                print(
                    "Abort: users already exist. Re-run with --allow-existing-users if intentional."
                )
                return 2

        if args.seed_rbac:
            summary = await seed_rbac(db)
            print(
                "RBAC seed complete:",
                f"permissions_created={summary['permissions_created']}",
                f"roles_created={summary['roles_created']}",
                f"role_permission_links_added={summary['role_permission_links_added']}",
            )

        if args.seed_sample_data:
            try:
                summary = await seed_sample_data(db)
                print("Sample data seed complete:")
                for key, value in summary.items():
                    print(f"  {key}: {value}")
            except Exception as exc:
                print(f"Sample data seeding failed: {exc}")
                return 4

        if args.bootstrap_admin:
            _require_admin_args(args)
            try:
                user = await bootstrap_admin_user(
                    db,
                    username=args.username,
                    email=args.email,
                    password=args.password,
                    role_name=args.role,
                )
            except BootstrapError as exc:
                print(f"Bootstrap failed: {exc}")
                return 3

            hydrated_user = await db.scalar(
                select(User)
                .options(selectinload(User.roles).selectinload(Role.permissions))
                .where(User.id == user.id)
            )
            role_names = sorted(
                role.name for role in (hydrated_user.roles if hydrated_user else user.roles)
            )
            print(
                "Admin bootstrap complete:",
                f"username={user.username}",
                f"email={user.email}",
                f"roles={','.join(role_names)}",
            )

    return 0


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    code = asyncio.run(_run(args))
    raise SystemExit(code)


if __name__ == "__main__":
    main()
