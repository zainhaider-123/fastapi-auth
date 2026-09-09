from settings import get_settings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

Base = declarative_base()

settings = get_settings()

engine = create_async_engine(settings.database_url)
SessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)


# Async database dependency
async def get_db():
    async with SessionLocal() as db:
        yield db
