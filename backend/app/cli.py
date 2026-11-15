"""Administrative commands that do not expose privileged setup over HTTP."""

import argparse
import getpass
import os

from pydantic import ValidationError
from sqlalchemy import select

from .database import SessionLocal
from .models import Role, User
from .schemas import UserCreate
from .security import hash_password
from .services.audit import record_audit


def create_admin(email: str, full_name: str, password: str) -> None:
    try:
        payload = UserCreate(email=email, full_name=full_name, password=password)
    except ValidationError as exc:
        raise SystemExit(str(exc)) from exc
    with SessionLocal() as db:
        normalized_email = str(payload.email).lower()
        if db.scalar(select(User).where(User.email == normalized_email)):
            raise SystemExit("Ya existe un usuario con ese correo")
        admin = User(
            email=normalized_email,
            full_name=payload.full_name,
            password_hash=hash_password(payload.password),
            role=Role.ADMIN,
        )
        db.add(admin)
        db.flush()
        record_audit(
            db,
            None,
            "INITIAL_ADMIN_CREATED",
            "USER",
            admin.id,
            {"role": Role.ADMIN.value},
        )
        db.commit()
        print(f"Administrador creado: {normalized_email}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    subcommands = parser.add_subparsers(dest="command", required=True)
    create = subcommands.add_parser("create-admin", help="Crea el primer administrador")
    create.add_argument("--email", required=True)
    create.add_argument("--name", required=True)
    create.add_argument("--password-env", default="INITIAL_ADMIN_PASSWORD")
    args = parser.parse_args()

    if args.command == "create-admin":
        password = os.getenv(args.password_env) or getpass.getpass("Contraseña segura: ")
        create_admin(args.email, args.name, password)


if __name__ == "__main__":
    main()
