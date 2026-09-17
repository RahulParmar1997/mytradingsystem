from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.user import RefreshToken, Role, RoleName, Session, User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
users_router = APIRouter(prefix="/api/v1/users", tags=["users"])
bearer = HTTPBearer(auto_error=False)


def user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        roles=[role.name for role in user.roles],
        is_active=user.is_active,
        is_email_verified=user.is_email_verified,
    )


async def get_or_create_role(db: AsyncSession, name: RoleName) -> Role:
    role = await db.scalar(select(Role).where(Role.name == name.value))
    if role:
        return role
    role = Role(name=name.value, description=f"{name.value} application role")
    db.add(role)
    await db.flush()
    return role


async def issue_session_tokens(db: AsyncSession, user: User, request: Request) -> TokenResponse:
    session = Session(
        user_id=user.id,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    db.add(session)
    await db.flush()
    access_token = create_access_token(str(user.id), session.id)
    refresh_token, expires_at = create_refresh_token(str(user.id), session.id)
    db.add(
        RefreshToken(
            user_id=user.id,
            session_id=session.id,
            token_hash=hash_token(refresh_token),
            expires_at=expires_at,
        )
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> UserResponse:
    email = str(payload.email).lower()
    existing = await db.scalar(select(User).where(User.email == email))
    if existing:
        raise HTTPException(status_code=409, detail="Email is already registered")

    user = User(email=email, password_hash=hash_password(payload.password))
    user.roles.append(await get_or_create_role(db, RoleName.USER))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user_response(user)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    email = str(payload.email).lower()
    user = await db.scalar(select(User).where(User.email == email))
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    tokens = await issue_session_tokens(db, user, request)
    await db.commit()
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing refresh token")
    raw_token = credentials.credentials
    try:
        claims = decode_token(raw_token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from exc
    if claims.get("type") != "refresh" or not claims.get("sub") or not claims.get("sid"):
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    token = await db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw_token)))
    now = datetime.now(timezone.utc)
    if not token or token.expires_at <= now:
        raise HTTPException(status_code=401, detail="Refresh token is invalid or expired")
    if token.revoked_at is not None:
        session = await db.get(Session, token.session_id)
        if session and session.revoked_at is None:
            session.revoked_at = now
            await db.commit()
        raise HTTPException(status_code=401, detail="Refresh token has been revoked")
    if str(token.user_id) != claims["sub"] or str(token.session_id) != claims["sid"]:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    session = await db.get(Session, token.session_id)
    user = await db.get(User, token.user_id)
    if not session or session.revoked_at is not None or not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Session is unavailable")

    token.revoked_at = now
    session.last_seen_at = now
    access_token = create_access_token(str(user.id), session.id)
    new_refresh, expires_at = create_refresh_token(str(user.id), session.id)
    replacement = RefreshToken(
        user_id=user.id,
        session_id=session.id,
        token_hash=hash_token(new_refresh),
        expires_at=expires_at,
    )
    db.add(replacement)
    await db.flush()
    token.replaced_by_id = replacement.id
    await db.commit()
    return TokenResponse(access_token=access_token, refresh_token=new_refresh)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> Response:
    if not credentials:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    try:
        claims = decode_token(credentials.credentials)
    except Exception:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    session_id = claims.get("sid")
    if session_id:
        try:
            session = await db.get(Session, UUID(session_id))
            if session and session.revoked_at is None:
                session.revoked_at = datetime.now(timezone.utc)
                await db.execute(
                    RefreshToken.__table__.update()
                    .where(RefreshToken.session_id == session.id, RefreshToken.revoked_at.is_(None))
                    .values(revoked_at=datetime.now(timezone.utc))
                )
                await db.commit()
        except (ValueError, TypeError):
            pass
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        claims = decode_token(credentials.credentials)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid access token") from exc
    if claims.get("type") != "access" or not claims.get("sub") or not claims.get("sid"):
        raise HTTPException(status_code=401, detail="Invalid access token")
    user = await db.get(User, claims["sub"])
    try:
        session = await db.get(Session, UUID(claims["sid"]))
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=401, detail="Invalid access token") from exc
    if not user or not user.is_active or not session or session.revoked_at is not None or session.user_id != user.id:
        raise HTTPException(status_code=401, detail="Session is unavailable")
    return user


@users_router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)) -> UserResponse:
    return user_response(user)
