from fastapi import FastAPI
from src.routes.accounts import router as account_router
from src.routes.movies import router as movie_router


app = FastAPI()

api_version_prefix = "/api/v1"

app.include_router(account_router, prefix=api_version_prefix)
app.include_router(movie_router, prefix=api_version_prefix)