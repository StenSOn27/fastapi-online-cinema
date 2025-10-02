from fastapi import FastAPI

from src.routes.accounts import router as accounts_router
from src.routes.movies import router as movies_router
from src.routes.moderator.moder_genres import router as genres_router
from src.routes.moderator.moder_movies import router as mod_movies_router
from src.routes.moderator.moder_stars import router as stars_router

app = FastAPI(
    title="Online Cinema API",
    version="1.0.0"
)

API_PREFIX = "/api/v1"

app.include_router(accounts_router, prefix=API_PREFIX, tags=["Accounts"])
app.include_router(movies_router, prefix=API_PREFIX, tags=["Movies"])
app.include_router(genres_router, prefix=API_PREFIX, tags=["Moderator - Genres"])
app.include_router(mod_movies_router, prefix=API_PREFIX, tags=["Moderator - Movies"])
app.include_router(stars_router, prefix=API_PREFIX, tags=["Moderator - Stars"])
