from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Organization, Role, User
from ..schemas import OrganizationCreate, OrganizationOut, UserAdminCreate, UserOut
from ..security import hash_password, require_roles
from ..services.audit import record_audit

router = APIRouter(prefix="/admin", tags=["Administración"])


@router.get("/organizations", response_model=list[OrganizationOut])
def organizations(
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(Role.ADMIN, Role.AUDITOR)),
):
    return list(db.scalars(select(Organization).order_by(Organization.name)))


@router.post("/organizations", response_model=OrganizationOut, status_code=201)
def create_organization(
    payload: OrganizationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN)),
):
    if db.scalar(select(Organization).where(Organization.name == payload.name)):
        raise HTTPException(status_code=409, detail="La organización ya existe")
    organization = Organization(**payload.model_dump())
    db.add(organization)
    db.flush()
    record_audit(
        db, user, "ORGANIZATION_CREATED", "ORGANIZATION", organization.id, payload.model_dump()
    )
    db.commit()
    db.refresh(organization)
    return organization


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserAdminCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(Role.ADMIN)),
):
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="El correo ya está registrado")
    if payload.role == Role.ORGANIZATION and not payload.organization_id:
        raise HTTPException(
            status_code=422, detail="El usuario de organización requiere organización"
        )
    if payload.organization_id and db.get(Organization, payload.organization_id) is None:
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    user = User(
        email=email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role=payload.role,
        organization_id=payload.organization_id,
    )
    db.add(user)
    db.flush()
    record_audit(db, actor, "USER_CREATED", "USER", user.id, {"role": user.role.value})
    db.commit()
    db.refresh(user)
    return user
