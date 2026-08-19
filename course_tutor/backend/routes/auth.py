import hashlib
import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from backend.db import SessionLocal
from backend.models import User, UserSession
from backend.schemas import AuthResponse, AuthUser, LoginRequest, RegisterRequest

router = APIRouter(prefix="/auth", tags=["auth"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(password: str, salt: str | None = None) -> str:
    resolved_salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        resolved_salt.encode("utf-8"),
        120000,
    ).hex()
    return f"{resolved_salt}${digest}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, existing_digest = stored_hash.split("$", 1)
    except ValueError:
        return False
    candidate = hash_password(password, salt).split("$", 1)[1]
    return secrets.compare_digest(candidate, existing_digest)


def create_session_token() -> str:
    return secrets.token_urlsafe(32)


def create_user_session(db: Session, user: User) -> UserSession:
    session = UserSession(user_id=user.id, session_token=create_session_token())
    db.add(session)
    db.flush()
    return session


def build_auth_response(user: User, token: str) -> AuthResponse:
    return AuthResponse(
        token=token,
        user=AuthUser(
            id=user.id,
            username=user.username,
            email=user.email,
        ),
    )


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    session = db.execute(
        select(UserSession)
        .where(UserSession.session_token == token)
        .options(selectinload(UserSession.user))
    ).scalar_one_or_none()
    if session:
        return session.user

    user = db.execute(select(User).where(User.session_token == token)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    return user


def get_optional_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User | None:
    if not authorization:
        return None
    return get_current_user(authorization=authorization, db=db)


@router.post("/register", response_model=AuthResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    username = payload.username.strip()
    email = payload.email.strip().lower()
    password = payload.password

    if len(username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
    if "@" not in email:
        raise HTTPException(status_code=400, detail="Enter a valid email address")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    existing = db.execute(
        select(User).where(
            or_(User.username == username, User.email == email)
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="An account with those details already exists")

    token = create_session_token()
    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        session_token=token,
    )
    db.add(user)
    db.flush()
    db.add(UserSession(user_id=user.id, session_token=token))
    db.commit()
    db.refresh(user)
    return build_auth_response(user, token)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    identifier = payload.username_or_email.strip()
    user = db.execute(
        select(User).where(
            or_(User.username == identifier, User.email == identifier.lower())
        )
    ).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid login credentials")

    session = create_user_session(db, user)
    db.commit()
    db.refresh(user)
    return build_auth_response(user, session.session_token)


@router.get("/me", response_model=AuthUser)
def me(current_user: User = Depends(get_current_user)):
    return AuthUser(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
    )
