from sqlalchemy import ForeignKey, Integer, String, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.models.base import Base


class Region(Base):
    __tablename__ = 'regions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)

    def __repr__(self):
        return f"<Region(id={self.id}, code={self.code}, name={self.name})>"


class MovieRegion(Base):
    __tablename__ = 'movie_regions'

    movie_id: Mapped[int] = mapped_column(Integer, ForeignKey('movies.id', ondelete='CASCADE'), primary_key=True)
    region_id: Mapped[int] = mapped_column(Integer, ForeignKey('regions.id'), primary_key=True)

    movie = relationship("Movie", backref="movie_regions")
    region = relationship("Region", backref="movie_regions")

    def __repr__(self):
        return f"<MovieRegion(movie_id={self.movie_id}, region_id={self.region_id})>"
