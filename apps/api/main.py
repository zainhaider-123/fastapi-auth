import uvicorn
from auth.routes import router as auth_router
from database.client import Base, engine
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

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


Base.metadata.create_all(bind=engine)


def main() -> None:
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
