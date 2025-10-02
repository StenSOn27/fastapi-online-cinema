from typing import List
from pydantic import BaseModel, ConfigDict

from src.schemas.movies import GenreSchema


class CartAddItemSchema(BaseModel):
    movie_id: int


class CartRemoveItemSchema(BaseModel):
    movie_id: int


class CartMovieItem(BaseModel):
    name: str
    year: int
    imdb: float
    genres: List[GenreSchema]

    model_config = ConfigDict(from_attributes=True)
