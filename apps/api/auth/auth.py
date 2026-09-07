from fastapi import APIRouter

from .model import LoginRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(request: LoginRequest):
    return {"message": "Hello, World!"}
