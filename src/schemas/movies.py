import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID


class MovieListItem(BaseModel):
    id: int
    uuid: UUID
    name: str
    year: int
    imdb: float
    price: float

    model_config = ConfigDict(from_attributes=True)


class MovieRetrieve(BaseModel):
    id: int
    uuid: UUID
    name: str
    year: int
    time: int
    imdb: float
    votes: int
    meta_score: Optional[float]
    gross: Optional[float]
    description: str
    price: float
    certification: str
    genres: List[str]
    directors: List[str]
    stars: List[str]

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
