import re
from typing import Tuple

from email_validator import validate_email, EmailNotValidError
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.crud import get_directors_by_ids, get_genres_by_ids, get_regions_by_ids, get_stars_by_ids
from src.schemas.movies import MovieCreate, MovieRetrieve


def validate_password_strength(password: str) -> str:
    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters.")
    if not re.search(r'[A-Z]', password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r'[a-z]', password):
        raise ValueError("Password must contain at least one lower letter.")
    if not re.search(r'\d', password):
        raise ValueError("Password must contain at least one digit.")
    if not re.search(r'[@$!%*?&#]', password):
        raise ValueError("Password must contain at least one special character: @, $, !, %, *, ?, #, &.")
    return password

def validate_email_address(email: str) -> str:
    try:

        # Check that the email address is valid. Turn on check_deliverability
        # for first-time validations like on account creation pages (but not
        # login pages).
        emailinfo = validate_email(email, check_deliverability=False)

        # After this point, use only the normalized form of the email address,
        # especially before going to a database query.
        email = emailinfo.normalized
        return email

    except EmailNotValidError as e:

        # The exception message is human-readable explanation of why it's
        # not a valid (or deliverable) email address.
        raise ValueError(str(e))


async def validate_movie_attributes(
    movie_data: MovieCreate,
    db: AsyncSession,
) -> Tuple:
    errors = []

    if not movie_data.certification_id:
        errors.append("Certification id must be provided")
    if not movie_data.genre_ids or movie_data.genre_ids == [0]:
        errors.append("At least 1 genre id must be provided")
    if not movie_data.star_ids or movie_data.star_ids == [0]:
        errors.append("At least 1 star id must be provided")
    if not movie_data.director_ids or movie_data.director_ids == [0]:
        errors.append("At least 1 director id must be provided")
    if not movie_data.regions_ids or movie_data.regions_ids == [0]:
        errors.append("At least 1 region id must be provided")

    if len(movie_data.genre_ids) != len(set(movie_data.genre_ids)):
        errors.append("Duplicate genre IDs in request")
    if len(movie_data.star_ids) != len(set(movie_data.star_ids)):
        errors.append("Duplicate star IDs in request")
    if len(movie_data.director_ids) != len(set(movie_data.director_ids)):
        errors.append("Duplicate director IDs in request")
    if len(movie_data.regions_ids) != len(set(movie_data.regions_ids)):
        errors.append("Duplicate region IDs in request")

    if errors:
        raise HTTPException(status_code=400, detail=errors)

    genres = await get_genres_by_ids(db, movie_data.genre_ids)
    stars = await get_stars_by_ids(db, movie_data.star_ids)
    directors = await get_directors_by_ids(db, movie_data.director_ids)
    regions = await get_regions_by_ids(db, movie_data.regions_ids)

    if len(genres) != len(movie_data.genre_ids):
        errors.append("Some genres not found")
    if len(stars) != len(movie_data.star_ids):
        errors.append("Some stars not found")
    if len(directors) != len(movie_data.director_ids):
        errors.append("Some directors not found")
    if len(regions) != len(movie_data.regions_ids):
        errors.append("Some regions not found")

    if errors:
        raise HTTPException(status_code=400, detail=errors)

    return genres, stars, directors, regions