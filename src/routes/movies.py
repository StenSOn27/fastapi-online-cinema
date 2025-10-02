from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from src.database.models.accounts import UserModel
from src.schemas.accounts import UserRetrieveSchema
from src.schemas.movies import (
    CommentCreate, CommentRetrieve,
    GenreCount, MovieListItem, MovieRetrieve
)
from src.database.models.movies import (
    Comment, Director, Favorite,
    Genre, Movie, MovieLike,
    Rating, Star, movie_genres
)
from src.config.dependencies import get_db, get_current_user
from sqlalchemy.orm import selectinload


router = APIRouter(prefix="/movies")

@router.get("/", response_model=List[MovieListItem])
async def movies_list(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1),
    page: int = Query(1, ge=1),
    year: int | None = Query(None),
    min_rating: float | None = Query(None),
    max_rating: float | None = Query(None),
    search: str | None = Query(None),
    sort_by: str = Query("release_date"),
    sort_order: str = Query("desc"),
):
    offset = (page - 1) * limit
    stmt = select(Movie).distinct()

    if search:
        stmt = stmt.join(Movie.directors, isouter=True).join(Movie.stars, isouter=True)
        stmt = stmt.where(
            sa.or_(
                Movie.name.ilike(f"%{search}%"),
                Movie.description.ilike(f"%{search}%"),
                Director.name.ilike(f"%{search}%"),
                Star.name.ilike(f"%{search}%")
            )
        )

    if year:
        stmt = stmt.where(Movie.year == year)
    if min_rating:
        stmt = stmt.where(Movie.imdb >= min_rating)
    if max_rating:
        stmt = stmt.where(Movie.imdb <= max_rating)

    sort_fields = {
        "release_date": Movie.year,
        "price": Movie.price,
        "rating": Movie.imdb,
        "popularity": Movie.votes,
    }

    sort_column = sort_fields.get(sort_by, Movie.year)
    if sort_order == "desc":
        stmt = stmt.order_by(sort_column.desc())
    else:
        stmt = stmt.order_by(sort_column.asc())

    stmt = stmt.limit(limit).offset(offset)

    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/genres/", response_model=List[GenreCount])
async def get_genres_with_counts(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(
            Genre.id,
            Genre.name,
            sa.func.count(movie_genres.c.movie_id).label("movie_count")
        )
        .join(movie_genres, movie_genres.c.genre_id == Genre.id, isouter=True)
        .group_by(Genre.id)
        .order_by(sa.desc("movie_count"))
    )
    result = await db.execute(stmt)
    rows = result.all()
    return [GenreCount(id=row.id, name=row.name, movie_count=row.movie_count) for row in rows]

@router.get("/{movie_id}/", response_model=MovieRetrieve)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)) -> MovieRetrieve:
    stmt = select(Movie).options(
        selectinload(Movie.certification),
        selectinload(Movie.genres),
        selectinload(Movie.directors),
        selectinload(Movie.stars),
    ).where(Movie.id == movie_id)

    result = await db.execute(stmt)
    movie = result.scalar_one_or_none()

    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")

    return MovieRetrieve.model_validate(movie)

@router.post("/{movie_id}/like")
async def like_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    user: UserRetrieveSchema = Depends(get_current_user)
) -> dict:
    movie = (await db.scalars(select(Movie).where(Movie.id == movie_id))).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    existing = (
        await db.scalars(
            select(MovieLike).where(
                MovieLike.user_id == user.id,
                MovieLike.movie_id == movie_id
            )
        )
    ).first()

    if existing:
        if existing.is_like:
            return {"message": "You already liked this movie"}
        else:
            existing.is_like = True
    else:
        db.add(MovieLike(user_id=user.id, movie_id=movie_id, is_like=True))

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Already liked")

    return {"message": "Movie liked"}

@router.post("/{movie_id}/dislike")
async def dislike_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    user: UserRetrieveSchema = Depends(get_current_user)
) -> dict:
    movie = (await db.scalars(select(Movie).where(Movie.id == movie_id))).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    existing = (
        await db.scalars(
            select(MovieLike).where(
                MovieLike.user_id == user.id,
                MovieLike.movie_id == movie_id
            )
        )
    ).first()

    if existing:
        if not existing.is_like:
            return {"message": "You already disliked this movie"}
        else:
            existing.is_like = False
    else:
        db.add(MovieLike(user_id=user.id, movie_id=movie_id, is_like=False))

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Already disliked")

    return {"message": "Movie disliked"}

@router.post("/{movie_id}/comments", response_model=CommentRetrieve, status_code=201)
async def create_comment(
    movie_id: int,
    comment_data: CommentCreate,
    db: AsyncSession = Depends(get_db),
    user: UserRetrieveSchema = Depends(get_current_user)
):
    movie = await db.get(Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    comment = Comment(
        user_id=user.id,
        movie_id=movie_id,
        text=comment_data.text
    )
    db.add(comment)

    try:
        await db.commit()
        await db.refresh(comment)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Error saving comment")

    return comment

@router.get("/{movie_id}/comments", response_model=List[CommentRetrieve])
async def get_comments(
    movie_id: int,
    db: AsyncSession = Depends(get_db)
) -> List[CommentRetrieve]:
    result = await db.execute(
        select(Comment)
        .where(Comment.movie_id == movie_id)
        .order_by(Comment.created_at.desc())
    )
    return result.scalars().all()

@router.post("/favorites/{movie_id}", status_code=201)
async def add_to_favorites(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    user: UserRetrieveSchema = Depends(get_current_user),
):
    movie = await db.scalar(select(Movie).where(Movie.id == movie_id))
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    existing = await db.scalar(
        select(Favorite).where(Favorite.user_id == user.id, Favorite.movie_id == movie_id)
    )
    if existing:
        raise HTTPException(status_code=400, detail="Already in favorites")

    db.add(Favorite(user_id=user.id, movie_id=movie_id))
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Already in favorites")

    return {"message": "Movie added to favorites"}

@router.delete("/favorites/{movie_id}", status_code=204)
async def remove_from_favorites(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    user: UserRetrieveSchema = Depends(get_current_user),
):
    favorite = await db.scalar(
        select(Favorite).where(Favorite.user_id == user.id, Favorite.movie_id == movie_id)
    )
    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite not found")

    await db.delete(favorite)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Could not remove favorite")

@router.get("/favorites", response_model=List[MovieListItem])
async def get_favorite_movies(
    db: AsyncSession = Depends(get_db),
    user: UserRetrieveSchema = Depends(get_current_user),
):
    stmt = (
        select(Movie)
        .join(Favorite, Movie.id == Favorite.movie_id)
        .where(Favorite.user_id == user.id)
        .order_by(Favorite.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/{movie_id}/rate")
async def rate_movie(
    movie_id: int,
    rating: int,
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user),
):
    if not (1 <= rating <= 10):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 10")

    movie = await db.get(Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    stmt = select(Rating).where(Rating.user_id == user.id, Rating.movie_id == movie_id)
    result = await db.execute(stmt)
    movie_rating = result.scalars().first()

    if movie_rating:
        movie_rating.rating = rating
    else:
        movie.votes += 1
        movie_rating = Rating(user_id=user.id, movie_id=movie_id, rating=rating)
        db.add(movie_rating)

    stmt = select(Rating.rating).where(Rating.movie_id == movie_id)
    result = await db.execute(stmt)
    ratings = result.scalars().all()

    if ratings:
        average_rating = sum(ratings) / len(ratings)
        movie.imdb = round(average_rating, 2)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Error saving rating")

    return {"message": "Rating saved"}
