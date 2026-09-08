from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..database.model import UserModel
from ..settings import Settings
from .schema import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    RegisterRequest,
    RegisterResponse,
    UserResponse,
)
from .utils import (
    generate_access_token,
    generate_refresh_token,
    hash_password,
    verify_password,
    verify_refresh_token,
)

settings = Settings()
router = APIRouter(prefix="/auth", tags=["auth"])

db_session = Annotated[AsyncSession, Depends(get_db)]


@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(data: RegisterRequest, db: db_session):
    existing_user_email = (
        await db.query(UserModel).filter(UserModel.email == data.email).first()
    )
    existing_user_username = (
        await db.query(UserModel).filter(UserModel.username == data.username).first()
    )
    if existing_user_email or existing_user_username:
        raise HTTPException(status_code=400, detail="User already exists")
    if data.password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    hashed_password = await hash_password(data.password)
    new_user = UserModel(
        name=data.name,
        email=data.email,
        username=data.username,
        password=hashed_password,
    )
    await db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return RegisterResponse(
        message="User created successfully", user=UserResponse.model_validate(new_user)
    )


@router.post("/login", response_model=LoginResponse, status_code=200)
async def login(data: LoginRequest, response: Response, db: db_session):
    user = await db.query(UserModel).filter(UserModel.email == data.email).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not await verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = await generate_access_token(user.id)
    refresh_token = await generate_refresh_token(user.id)

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.access_token_expires_in,
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
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

    user_id = await verify_refresh_token(refresh_token)

    user = await db.query(UserModel).filter(UserModel.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found",
        )

    access_token = await generate_access_token(user.id)

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.access_token_expires_in,
    )

    return RefreshTokenResponse(message="Access token refreshed")
