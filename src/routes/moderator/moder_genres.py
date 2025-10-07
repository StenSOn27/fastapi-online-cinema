from fastapi import APIRouter, Depends, HTTPException

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.schemas.movies import GenreSchema
from src.database.models.movies import Genre, movie_genres
from src.config.dependencies import get_db, require_roles


router = APIRouter(prefix="/movies/genres")

@router.post("/", response_model=GenreSchema, dependencies=[Depends(require_roles(["moderator"]))])
async def create_genre(name: str, db: AsyncSession = Depends(get_postgresql_db)):
    genre = Genre(name=name)
    db.add(genre)
    try:
        await db.commit()
        await db.refresh(genre)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Genre already exists")

    return GenreSchema.model_validate(genre)


@router.put("/{genre_id}/", response_model=GenreSchema, dependencies=[Depends(require_roles(["moderator"]))])
async def update_genre(genre_id: int, name: str, db: AsyncSession = Depends(get_postgresql_db)):
    genre = await db.get(Genre, genre_id)
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")

    genre.name = name
    try:
        await db.commit()
        await db.refresh(genre)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Failed to update genre")

    count_stmt = select(sa.func.count()).select_from(movie_genres).where(movie_genres.c.genre_id == genre.id)
    result = await db.execute(count_stmt)
    movie_count = result.scalar()

    return GenreSchema.model_validate(genre)

@router.delete("/{genre_id}/", status_code=204, dependencies=[Depends(require_roles(["moderator"]))])
async def delete_genre(genre_id: int, db: AsyncSession = Depends(get_postgresql_db)):
    genre = await db.get(Genre, genre_id)
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")

    await db.delete(genre)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Cannot delete genre (possibly in use)")
