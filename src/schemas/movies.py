from typing import List, Optional
from pydantic import BaseModel, ConfigDict
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
