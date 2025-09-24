from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.movies import MovieListItem, MovieRetrieve
from src.database.models.movies import Movie, MovieLike, ReactionType, User
from src.config.dependencies import get_db, get_current_user


router = APIRouter(prefix="/movies")

@router.get("/", response_model=List[MovieListItem])
async def movies_list(
        db: AsyncSession = Depends(get_db),
        limit: int = Query(10, ge=0),
        offset: int = Query(0, ge=0)
) -> List:
    return [movie for movie in await db.scalars(select(Movie).limit(limit).offset(offset))]

@router.get("/{movie_id}/", response_model=MovieRetrieve)
async def get_movie(
    movie_id: int, db: AsyncSession = Depends(get_db)
) -> MovieRetrieve:
    movie = (await db.scalars(select(Movie).where(Movie.id == movie_id))).first()
    return MovieRetrieve.model_validate(movie)
