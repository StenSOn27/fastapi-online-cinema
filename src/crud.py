import datetime
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database.models.accounts import ActivationTokenModel, UserModel
from src.database.models.movies import Genre, Star, Director


async def get_user_by_email(db: AsyncSession, email: str) -> UserModel | None:
    """Retrieve a user by their email address."""

    result = await db.execute(select(UserModel).where(UserModel.email == email))
    return result.scalar_one_or_none()


def delete_expired_tokens(db):
    now = datetime.datetime.now(datetime.timezone.utc)
    db.query(ActivationTokenModel).filter(
        ActivationTokenModel.expires_at < now
    ).delete(synchronize_session=False)
    db.commit()


async def get_genres_by_ids(db: AsyncSession, ids: list[int]) -> list[Genre]:
    result = await db.execute(select(Genre).where(Genre.id.in_(ids)))
    return result.scalars().all()


async def get_stars_by_ids(db: AsyncSession, ids: list[int]) -> list[Star]:
    result = await db.execute(select(Star).where(Star.id.in_(ids)))
    return result.scalars().all()


async def get_directors_by_ids(db: AsyncSession, ids: list[int]) -> list[Director]:
    result = await db.execute(select(Director).where(Director.id.in_(ids)))
    return result.scalars().all()