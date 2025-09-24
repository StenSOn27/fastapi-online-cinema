from typing import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import (
    create_async_engine, async_sessionmaker, AsyncSession
)

DATABASE_URL = "sqlite+aiosqlite:///./database.db"
DATABASE_URL_SYNC = "sqlite:///./database.db"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)

sync_engine = create_engine(DATABASE_URL_SYNC, echo=True)
SessionLocal = sessionmaker(bind=sync_engine, autoflush=False, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as db:
        yield db
