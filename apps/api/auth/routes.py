from typing import Annotated

from auth.schema import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    RefreshTokenResponse,
    RegisterRequest,
    RegisterResponse,
    UserResponse,
)
from auth.utils import (
    generate_access_token,
    generate_refresh_token,
    hash_password,
    verify_password,
    verify_refresh_token,
)
from database.client import get_db
from database.model.user import UserModel
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from settings import Settings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

settings = Settings()
router = APIRouter(prefix="/auth", tags=["auth"])

db_session = Annotated[AsyncSession, Depends(get_db)]


@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(data: RegisterRequest, db: db_session):
    existing_user_email = (
        await db.execute(select(UserModel).where(UserModel.email == data.email))
    ).scalar_one_or_none()
    existing_user_username = (
        await db.execute(select(UserModel).where(UserModel.username == data.username))
    ).scalar_one_or_none()
    if existing_user_email or existing_user_username:
        raise HTTPException(status_code=400, detail="User already exists")
    if data.password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    hashed_password = hash_password(data.password)
    new_user = UserModel(
        name=data.name,
        email=data.email,
        username=data.username,
        password=hashed_password,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return RegisterResponse(
        message="User created successfully", user=UserResponse.model_validate(new_user)
    )


@router.post("/login", response_model=LoginResponse, status_code=200)
async def login(data: LoginRequest, response: Response, db: db_session):
    user = (
        await db.execute(select(UserModel).where(UserModel.email == data.email))
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = generate_access_token(user.id)
    refresh_token = generate_refresh_token(user.id)

    response.set_cookie(
        key="access_token",
        value=access_token,
        # httponly=True,
        # secure=True,
        samesite="lax",
        max_age=settings.access_token_expires_in,
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        # httponly=True,
        # secure=True,
        samesite="lax",
        max_age=settings.refresh_token_expires_in,
        path="/api/v1/auth/refresh",
    )

    return LoginResponse(message="Login successful")


@router.post("/logout", response_model=LogoutResponse, status_code=200)
async def logout(response: Response):
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    return LogoutResponse(message="Logout successful")


@router.post("/refresh", response_model=RefreshTokenResponse, status_code=200)
async def refresh(
    response: Response,
    db: db_session,
    refresh_token: str | None = Cookie(default=None),
):
    if not refresh_token:
        raise HTTPException(
            status_code=401,
            detail="Refresh token is required",
        )

    user_id = verify_refresh_token(refresh_token)

    user = (
        await db.execute(select(UserModel).where(UserModel.id == user_id))
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found",
        )

    access_token = generate_access_token(user.id)

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.access_token_expires_in,
    )

    return RefreshTokenResponse(message="Access token refreshed")
