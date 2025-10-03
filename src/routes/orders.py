from typing import List
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException

from src.schemas.orders import OrderSchema
from src.config.dependencies import get_current_user
from src.schemas.accounts import UserRetrieveSchema
from src.database.session_sqlite import get_db
from src.crud import split_available_movies
from src.database.models.movies import Movie
from src.database.models.shopping_cart import Cart, CartItem
from src.database.models.orders import Order, OrderItem
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/orders")

@router.post("/create/")
async def create_order_from_cart(
    current_user: UserRetrieveSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cart_movie_ids = (await db.execute(
        sa.select(CartItem.movie_id)
        .join(Cart, CartItem.cart_id == Cart.id)
        .where(Cart.user_id == current_user.id)
    )).scalars().all()

    if not cart_movie_ids:
        raise HTTPException(status_code=400, detail="Cart is empty")

    available_ids, unavailable_ids = await split_available_movies(db, cart_movie_ids, current_user.region.code)

    if not available_ids:
        return {
            "order_created": False,
            "unavailable_movie_ids": unavailable_ids,
            "message": "All movies are unavailable and were excluded from order."
        }

    order = Order(user_id=current_user.id)
    db.add(order)
    await db.flush()

    movies = (await db.execute(
        sa.select(Movie.id, Movie.price)
        .where(Movie.id.in_(available_ids))
    )).all()

    total = 0
    for m_id, price in movies:
        db.add(OrderItem(order_id=order.id, movie_id=m_id, price_at_order=price))
        total += price

    order.total_amount = total
    await db.commit()

    return {
        "order_created": True,
        "order_id": order.id,
        "total_amount": str(total),
        "excluded_movie_ids": unavailable_ids,
        "message": (
            "Some movies were excluded due to unavailability."
            if unavailable_ids else
            "All movies included."
        )
    }


@router.get("/", response_model=List[OrderSchema])
async def get_orders_list(
    db: AsyncSession = Depends(get_db),
    current_user: UserRetrieveSchema = Depends(get_current_user),
) -> List[OrderSchema]:

    stmt = (
        sa.select(Order)
        .options(selectinload(Order.items))
        .where(Order.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    orders = result.scalars().all()

    if not orders:
        raise HTTPException(status_code=404, detail="You have no orders")
    
    return orders
