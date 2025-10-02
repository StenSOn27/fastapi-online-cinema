import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, UUID4 as UUID, Field
from decimal import Decimal


class MovieListItem(BaseModel):
    id: int
    uuid: UUID
    name: str
    year: int
    imdb: float
    price: float

    model_config = ConfigDict(from_attributes=True)


class CommentCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)


class CommentRetrieve(BaseModel):
    id: int
    user_id: int
    movie_id: int
    text: str
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class GenreCount(BaseModel):
    id: int
    name: str
    movie_count: int

    model_config = ConfigDict(from_attributes=True)


class MoviesByGenre(BaseModel):
    genre_id: int
    genre_name: str
    movies: List[MovieListItem]

    model_config = ConfigDict(from_attributes=True)


class GenreSchema(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class StarSchema(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class DirectorSchema(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class CertificationSchema(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class MovieCreate(BaseModel):
    name: str
    year: int
    time: int
    description: str
    price: float
    certification_id: int
    genre_ids: List[int] = []
    star_ids: List[int] = []
    director_ids: List[int] = []

    model_config = ConfigDict(from_attributes=True)

class MovieUpdate(BaseModel):
    name: str
    year: int
    time: int
    imdb: Optional[float] = None
    votes: int
    meta_score: Optional[float] = None
    gross: Optional[float] = None
    description: str
    price: float
    certification_id: int
    genre_ids: List[int] = []
    star_ids: List[int] = []
    director_ids: List[int] = []

    model_config = ConfigDict(from_attributes=True)

class MovieRetrieve(BaseModel):
    id: int
    uuid: UUID
    name: str
    year: int
    time: int
    imdb: float
    votes: int
    meta_score: Optional[float] = None
    gross: Optional[float] = None
    description: str
    price: float
    certification: CertificationSchema
    genres: List[GenreSchema]
    stars: List[StarSchema]
    directors: List[DirectorSchema]

    model_config = ConfigDict(from_attributes=True)
