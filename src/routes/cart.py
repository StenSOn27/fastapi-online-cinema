from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from src.database.models.movies import Movie, PurchasedMovie
from src.database.models.shopping_cart import Cart, CartItem
from src.database.session_postgres import get_postgresql_db
from src.config.dependencies import get_current_user
from src.schemas.accounts import UserRetrieveSchema
from src.schemas.cart import CartAddItemSchema, CartRemoveItemSchema, CartMovieItem

router = APIRouter(prefix="/cart")

@router.post("/add/", response_model=CartMovieItem)
async def add_movie_to_cart(
    item: CartAddItemSchema,
    current_user: UserRetrieveSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgresql_db),
):
    result = await db.execute(
        select(Cart).where(Cart.user_id == current_user.id)
    )
    cart = result.scalar_one_or_none()
    if cart is None:
        cart = Cart(user_id=current_user.id)
        db.add(cart)
        await db.commit()
        await db.refresh(cart)

    purchased_result = await db.execute(
        select(PurchasedMovie)
        .where(PurchasedMovie.user_id == current_user.id)
        .where(PurchasedMovie.movie_id == item.movie_id)
    )
    purchased = purchased_result.scalar_one_or_none()
    if purchased:
        raise HTTPException(
            status_code=400,
            detail="You have already purchased this movie and cannot buy it again."
        )

    cart_item_result = await db.execute(
        select(CartItem)
        .where(CartItem.cart_id == cart.id)
        .where(CartItem.movie_id == item.movie_id)
    )
    existing_cart_item = cart_item_result.scalar_one_or_none()
    if existing_cart_item:
        raise HTTPException(
            status_code=400,
            detail="Movie is already in your cart."
        )
    
    movie_result = await db.execute(
        select(Movie)
        .options(selectinload(Movie.genres))
        .where(Movie.id == item.movie_id)
    )
    movie = movie_result.scalar_one_or_none()
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")

    new_cart_item = CartItem(cart_id=cart.id, movie_id=item.movie_id)
    db.add(new_cart_item)
    await db.commit()
    await db.refresh(new_cart_item)

    return CartMovieItem.model_validate(movie)

@router.get("/", response_model=List[CartMovieItem])
async def get_cart(
    current_user: UserRetrieveSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgresql_db),
):
    result = await db.execute(
        select(CartItem)
        .join(Cart)
        .where(Cart.user_id == current_user.id)
        .options(
            selectinload(CartItem.movie)
            .selectinload(Movie.genres)
        )
    )
    cart_items = result.scalars().all()
    return [CartMovieItem.model_validate(item.movie) for item in cart_items]

@router.delete("/remove/", status_code=204)
async def remove_movie_from_cart(
    item: CartRemoveItemSchema,
    current_user: UserRetrieveSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgresql_db),
):
    try:
        result = await db.execute(
            select(Cart).where(Cart.user_id == current_user.id)
        )
        cart = result.scalar_one_or_none()
        if not cart:
            return

        result = await db.execute(
            select(CartItem)
            .where(CartItem.cart_id == cart.id)
            .where(CartItem.movie_id == item.movie_id)
        )
        cart_item = result.scalar_one_or_none()
        if not cart_item:
            return

        await db.delete(cart_item)
        await db.commit()

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred")


from sqlalchemy import delete

@router.delete("/clear/", status_code=204)
async def clear_cart(
    current_user: UserRetrieveSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgresql_db),
):
    try:
        result = await db.execute(
            select(Cart).where(Cart.user_id == current_user.id)
        )
        cart = result.scalar_one_or_none()
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")

        delete_stmt = delete(CartItem).where(CartItem.cart_id == cart.id)
        await db.execute(delete_stmt)
        await db.commit()

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred")
