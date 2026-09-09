from contextlib import asynccontextmanager

import uvicorn
from auth.routes import router as auth_router
from database.client import Base, engine
from database.model.user import UserModel  # noqa: F401 — register model metadata
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api = APIRouter(prefix="/api/v1")


# API routes
api.include_router(auth_router)


@api.get("/healthz")
def health_check():
    return {"status": "ok"}


# Register routers
app.include_router(api)


def main() -> None:
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
