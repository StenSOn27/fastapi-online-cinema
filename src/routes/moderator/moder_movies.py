from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from src.database.validators import validate_movie_attributes
from src.schemas.movies import MovieCreate, MovieRetrieve, MovieUpdate
from src.database.models.movies import Movie
from src.config.dependencies import get_db, require_roles
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/movies")

@router.post("/", response_model=MovieRetrieve, dependencies=[Depends(require_roles(["moderator"]))])
async def create_movie(
    movie_data: MovieCreate,
    db: AsyncSession = Depends(get_db),
) -> MovieRetrieve:

    genres, stars, directors, regions = await validate_movie_attributes(movie_data, db)

    new_movie = Movie(
        name=movie_data.name,
        year=movie_data.year,
        time=movie_data.time,
        description=movie_data.description,
        price=movie_data.price,
        certification_id=movie_data.certification_id,
        genres=genres,
        stars=stars,
        directors=directors,
        regions=regions
    )

    db.add(new_movie)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Movie with this data already exists")

    stmt = (
        select(Movie)
        .options(
            selectinload(Movie.certification),
            selectinload(Movie.genres),
            selectinload(Movie.directors),
            selectinload(Movie.stars),
            selectinload(Movie.regions),
        )
        .where(Movie.id == new_movie.id)
    )
    result = await db.execute(stmt)
    movie_with_relations = result.scalar_one()

    return MovieRetrieve.model_validate(movie_with_relations)

from sqlalchemy.orm import selectinload

@router.put("/{movie_id}/", response_model=MovieRetrieve, dependencies=[Depends(require_roles(["moderator"]))])
async def update_movie(
    movie_id: int,
    movie_data: MovieUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Movie)
        .options(
            selectinload(Movie.genres),
            selectinload(Movie.stars),
            selectinload(Movie.directors),
            selectinload(Movie.certification),
            selectinload(Movie.regions),
        )
        .where(Movie.id == movie_id)
    )
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    genres, stars, directors, regions = await validate_movie_attributes(movie_data, db)

    movie.name = movie_data.name
    movie.year = movie_data.year
    movie.time = movie_data.time
    movie.description = movie_data.description
    movie.price = movie_data.price
    movie.certification_id = movie_data.certification_id
    movie.genres = genres
    movie.stars = stars
    movie.directors = directors
    movie.regions = regions

    try:
        await db.commit()
        await db.refresh(movie)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Failed to update movie")

    return MovieRetrieve.model_validate(movie)


@router.delete("/{movie_id}/", status_code=204, dependencies=[Depends(require_roles(["moderator"]))])
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    movie = await db.get(Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    await db.delete(movie)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Failed to delete movie")
