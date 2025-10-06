import datetime
import sqlalchemy as sa
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database.models.accounts import ActivationTokenModel, UserModel
from src.database.models.movies import Genre, Movie, Star, Director
from src.database.models.regions import MovieRegion, Region


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


async def get_regions_by_ids(db: AsyncSession, ids: list[int]) -> list[Region]:
    result = await db.execute(select(Region).where(Region.id.in_(ids)))
    return result.scalars().all()


async def split_available_movies(
    db: AsyncSession,
    movie_ids: List[int],
    user_region: str
) -> Tuple[List[int], List[int]]:
    result_existing = await db.execute(
        sa.select(Movie.id).where(Movie.id.in_(movie_ids))
    )
    existing_ids = {row[0] for row in result_existing.all()}

    valid_movie_ids = list(existing_ids)

    result_region = await db.execute(
        sa.select(MovieRegion.movie_id)
        .join(Region, MovieRegion.region_id == Region.id)
        .where(
            MovieRegion.movie_id.in_(valid_movie_ids),
            Region.code == user_region
        )
    )
    available_ids = {row[0] for row in result_region.all()}

    unavailable_ids = set(movie_ids) - available_ids

    return list(available_ids), list(unavailable_ids)
