from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.accounts import UserModel
from schemas.accounts import UserRetrieveSchema
from schemas.movies import CommentCreate, CommentRetrieve, MovieListItem, MovieRetrieve
from src.database.models.movies import Comment, Director, Favorite, Movie, MovieLike, Star
from src.config.dependencies import get_db, get_current_user
from sqlalchemy.exc import IntegrityError


router = APIRouter(prefix="/movies")

@router.get("/", response_model=List[MovieListItem])
async def movies_list(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    year: int | None = Query(None),
    min_rating: float | None = Query(None),
    max_rating: float | None = Query(None),
    search: str | None = Query(None),
    sort_by: str = Query("release_date"),
    sort_order: str = Query("desc"),
):
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
    stmt = stmt.order_by(sort_column.asc())

    stmt = stmt.limit(limit).offset(offset)

    result = await db.execute(stmt)
    return result.scalars().all()


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
    user: UserRetrieveSchema = Depends(get_current_user)
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
    user: UserRetrieveSchema = Depends(get_current_user)
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
    await db.commit()
    await db.refresh(comment)
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

    comments = result.scalars().all()
    return comments

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
    await db.commit()
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
    await db.commit()

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
