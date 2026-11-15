from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models import Role, User
from ..rate_limit import LoginRateLimiter
from ..schemas import LoginRequest, TokenOut, UserCreate, UserOut
from ..security import create_access_token, get_current_user, hash_password, verify_password
from ..services.audit import record_audit

router = APIRouter(prefix="/auth", tags=["Autenticación"])
settings = get_settings()
login_limiter = LoginRateLimiter(
    settings.login_rate_limit_attempts,
    settings.login_rate_limit_window_seconds,
)


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="El correo ya está registrado")
    user = User(
        email=email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role=Role.DONOR,
    )
    db.add(user)
    db.flush()
    record_audit(db, user, "USER_REGISTERED", "USER", user.id, {"role": user.role.value})
    db.commit()
    db.refresh(user)
    return TokenOut(access_token=create_access_token(user), user=user)


@router.post("/login", response_model=TokenOut)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    client_host = request.client.host if request.client else "unknown"
    limiter_key = f"{client_host}:{payload.email.lower()}"
    retry_after = login_limiter.check(limiter_key)
    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos. Intenta nuevamente más tarde",
            headers={"Retry-After": str(retry_after)},
        )
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not user.active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Correo o contraseña incorrectos"
        )
    login_limiter.clear(limiter_key)
    return TokenOut(access_token=create_access_token(user), user=user)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
