import uvicorn
from auth.auth import router as auth_router
from database.client import Base, engine
from fastapi import FastAPI

app = FastAPI()

app.include_router(auth_router)

Base.metadata.create_all(bind=engine)


@app.get("/")
async def read_root():
    return {"message": "Hello, World!"}


def main() -> None:
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
