from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from src.database.models.movies import Movie
from src.database.models.shopping_cart import Cart, CartItem
from src.database.session_postgres import get_postgresql_db
from src.config.dependencies import require_roles
from src.schemas.accounts import UserRetrieveSchema
from src.schemas.cart import CartMovieItem

router = APIRouter(prefix="/cart/admin")

@router.get(
    "/user/{user_id}",
    response_model=List[CartMovieItem],
    dependencies=[Depends(require_roles(["ADMIN"]))]
)
async def get_user_cart(
    user_id: int,
    db: AsyncSession = Depends(get_postgresql_db),
):
    try:
        result = await db.execute(
            select(CartItem)
            .join(Cart)
            .where(Cart.user_id == user_id)
            .options(
                selectinload(CartItem.movie).selectinload(Movie.genres)
            )
        )
        cart_items = result.scalars().all()
    
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="An unexpected database error occurred while retrieving the user's cart. Please try again later."
        )

    return [CartMovieItem.model_validate(item.movie) for item in cart_items]