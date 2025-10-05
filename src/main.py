from fastapi import FastAPI

from src.routes.accounts import router as accounts_router
from src.routes.movies import router as movies_router
from src.routes.cart import router as cart_router 
from src.routes.moderator.moder_genres import router as genres_router
from src.routes.moderator.moder_movies import router as mod_movies_router
from src.routes.moderator.moder_stars import router as stars_router
from src.routes.admin.admin_cart import router as admin_cart_router
from src.routes.regions import router as regions_router
from src.routes.orders import router as orders_router
from src.routes.admin.admin_orders import router as admin_orders_router
from src.routes.payment import router as payment_router
from src.routes.admin.payment import router as admin_payment_router


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
app.include_router(cart_router, prefix=API_PREFIX, tags=["Shoping Cart"])
app.include_router(admin_cart_router, prefix=API_PREFIX, tags=["Admin - Shoping Cart"])
app.include_router(regions_router, prefix=API_PREFIX, tags=["Regions"])
app.include_router(orders_router, prefix=API_PREFIX, tags=["Orders"])
app.include_router(admin_orders_router, prefix=API_PREFIX, tags=["Admin - Orders"])
app.include_router(payment_router, prefix=API_PREFIX, tags=["Payment"])
app.include_router(admin_payment_router, prefix=API_PREFIX, tags=["Admin - Payment"])
