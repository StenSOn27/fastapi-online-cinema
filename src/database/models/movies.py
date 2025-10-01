import datetime
from typing import List
from sqlalchemy import (
    Boolean, Column, DateTime, Integer, String, Text, ForeignKey,
    Table, UniqueConstraint, DECIMAL, Enum
)
from src.database.models.accounts import UserModel
from src.database.models.base import Base
from sqlalchemy.orm import (
    Mapped, mapped_column, relationship
)
import uuid
from uuid import UUID
from enum import Enum as PyEnum

movie_genres = Table(
    "movie_genres",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id"), primary_key=True),
    Column("genre_id", ForeignKey("genres.id"), primary_key=True),
)

movie_stars = Table(
    "movie_stars",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id"), primary_key=True),
    Column("star_id", ForeignKey("stars.id"), primary_key=True),
)

movie_directors = Table(
    "movie_directors",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id"), primary_key=True),
    Column("director_id", ForeignKey("directors.id"), primary_key=True),
)


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    movies: Mapped[list["Movie"]] = relationship(
        secondary=movie_genres,
        back_populates="genres"
    )


class Star(Base):
    __tablename__ = "stars"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    movies: Mapped[list["Movie"]] = relationship(
        secondary=movie_stars,
        back_populates="stars"
    )


class Director(Base):
    __tablename__ = "directors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    movies: Mapped[list["Movie"]] = relationship(
        secondary=movie_directors,
        back_populates="directors"
    )


class Certification(Base):
    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    movies: Mapped[list["Movie"]] = relationship(
        back_populates="certification"
    )


class Movie(Base):
    __tablename__ = "movies"
    __table_args__ = (
        UniqueConstraint("name", "year", "time", name="uq_movie_name_year_time"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[UUID] = mapped_column(default=uuid.uuid4, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)
    time: Mapped[int] = mapped_column(nullable=False)
    imdb: Mapped[float] = mapped_column(nullable=False)
    votes: Mapped[int] = mapped_column(nullable=False)
    meta_score: Mapped[float | None] = mapped_column(nullable=True)
    gross: Mapped[float | None] = mapped_column(nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    certification_id: Mapped[int] = mapped_column(ForeignKey("certifications.id"), nullable=False)

    likes: Mapped[List["MovieLike"]] = relationship("MovieLike", back_populates="movie")
    certification: Mapped["Certification"] = relationship(back_populates="movies")

    genres: Mapped[list["Genre"]] = relationship(
        secondary=movie_genres,
        back_populates="movies"
    )
    stars: Mapped[list["Star"]] = relationship(
        secondary=movie_stars,
        back_populates="movies"
    )
    directors: Mapped[list["Director"]] = relationship(
        secondary=movie_directors,
        back_populates="movies"
    )


class Favorite(Base):
    __tablename__ = "favorites"
    user_id = Column(ForeignKey("users.id"), primary_key=True)
    movie_id = Column(ForeignKey("movies.id"), primary_key=True)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))


class MovieLike(Base):
    __tablename__ = "movie_likes"
    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", name="uq_user_movie_like"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), nullable=False)
    is_like: Mapped[Boolean] = mapped_column(Boolean, nullable=False)

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="likes")
    movie: Mapped["Movie"] = relationship("Movie", back_populates="likes")


class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey("users.id"))
    movie_id = Column(ForeignKey("movies.id"))
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))


class Rating(Base):
    __tablename__ = "ratings"
    user_id = Column(ForeignKey("users.id"), primary_key=True)
    movie_id = Column(ForeignKey("movies.id"), primary_key=True)
    rating = Column(Integer)


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey("users.id"))
    type = Column(String)
    message = Column(Text)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
