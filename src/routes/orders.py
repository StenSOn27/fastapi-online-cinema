from typing import List
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException

from src.config.settings import BaseAppSettings
from src.schemas.orders import OrderSchema
from src.config.dependencies import get_checkout_session, get_current_user, get_settings
from src.schemas.accounts import UserRetrieveSchema
from src.database.session_sqlite import get_db
from src.crud import split_available_movies
from src.database.models.movies import Movie
from src.database.models.shopping_cart import Cart, CartItem
from src.database.models.orders import Order, OrderItem, OrderStatus
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError


router = APIRouter(prefix="/orders")

@router.post("/create/")
async def create_order_from_cart(
    current_user: UserRetrieveSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cart_movie_ids = (await db.execute(
        sa.select(CartItem.movie_id)
        .distinct()
        .join(Cart, CartItem.cart_id == Cart.id)
        .where(Cart.user_id == current_user.id)
    )).scalars().all()

    if not cart_movie_ids:
        raise HTTPException(status_code=400, detail="Cart is empty")

    purchased_ids = (await db.execute(
        sa.select(OrderItem.movie_id)
        .join(Order, OrderItem.order_id == Order.id)
        .where(Order.user_id == current_user.id)
        .where(Order.status == OrderStatus.PAID)
    )).scalars().all()

    movie_ids_to_check = list(set(cart_movie_ids) - set(purchased_ids))

    if not movie_ids_to_check:
        raise HTTPException(status_code=400, detail="All movies in cart already purchased")

    available_ids, unavailable_ids = await split_available_movies(db, movie_ids_to_check, current_user.region.code)

    if not available_ids:
        return {
            "order_created": False,
            "unavailable_movie_ids": unavailable_ids,
            "message": "All movies are unavailable or already purchased"
        }

    pending_ids = (await db.execute(
        sa.select(OrderItem.movie_id)
        .join(Order, OrderItem.order_id == Order.id)
        .where(Order.user_id == current_user.id)
        .where(Order.status == OrderStatus.PENDING)
    )).scalars().all()

    final_movie_ids = list(set(available_ids) - set(pending_ids))

    if not final_movie_ids:
        raise HTTPException(status_code=400, detail="All movies already included in a pending order")

    order = Order(user_id=current_user.id)
    db.add(order)
    await db.flush()

    movies = (await db.execute(
        sa.select(Movie.id, Movie.price)
        .where(Movie.id.in_(final_movie_ids))
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
        "excluded_movie_ids": list(set(cart_movie_ids) - set(final_movie_ids)),
        "message": (
            "Some movies were excluded (unavailable, already purchased or already in a pending order)."
            if len(final_movie_ids) < len(cart_movie_ids) else
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

@router.patch("/cancel/")
async def cancel_order_before_payment(
    order_id: int,
    current_user: UserRetrieveSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        stmt = (
            sa.select(Order)
            .where(Order.user_id == current_user.id)
            .where(Order.id == order_id)
        )
        result = await db.execute(stmt)
        order = result.scalars().first()

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if order.status == OrderStatus.PAID:
            raise HTTPException(status_code=400, detail="Cannot cancel a paid order")
        if order.status == OrderStatus.CANCELED:
            raise HTTPException(status_code=400, detail="Order already canceled")
        
        order.status = OrderStatus.CANCELED
        await db.commit()

    except IntegrityError:
        raise HTTPException(status_code=500, detail="Error during canceling order, try again")

    return {"message": "Order canceled successfully"}


@router.post("/confirm/")
async def confirm_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    user: UserRetrieveSchema = Depends(get_current_user),
    settings: BaseAppSettings = Depends(get_settings)
) -> dict:
    
    session = await get_checkout_session(
        order_id=order_id,
        db=db,
        user=user,
        settings=settings
    )
    return session