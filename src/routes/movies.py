from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.movies import MovieListItem, MovieRetrieve
from src.database.models.movies import Movie, MovieLike, ReactionType, User
from src.config.dependencies import get_db, get_current_user
from sqlalchemy.exc import IntegrityError


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

@router.post("/{movie_id}/like")
async def like_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
) -> dict:

    movie = (await db.scalars(select(Movie).where(Movie.id == movie_id))).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    like = MovieLike(user_id=user.id, movie_id=movie_id, is_like=True)

    try:
        db.add(like)
        await db.commit()
    except IntegrityError:
        raise HTTPException(status_code=400, detail="You already liked this movie")

    return {"message": "Movie liked"}

@router.post("/{movie_id}/dislike")
async def dislike_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
) -> dict:

    movie = (await db.scalars(select(Movie).where(Movie.id == movie_id))).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    dislike = MovieLike(user_id=user.id, movie_id=movie_id, is_like=False)

    try:
        db.add(dislike)
        await db.commit()
    except IntegrityError:
        raise HTTPException(status_code=400, detail="You already disliked this movie")

    return {"message": "Movie disliked"}

