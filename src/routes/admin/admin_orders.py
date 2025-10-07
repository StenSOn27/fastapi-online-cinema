from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import date

from src.database.models.orders import Order, OrderStatus
from src.schemas.orders import OrderSchema
from src.config.dependencies import get_db, require_roles


router = APIRouter(prefix="/admin/orders")

@router.get("/", response_model=List[OrderSchema], dependencies=[Depends(require_roles(["ADMIN"]))])
async def get_all_orders_for_admin(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    status: Optional[OrderStatus] = Query(None, description="Filter by order status"),
    from_date: Optional[date] = Query(None, description="Filter orders from this date", example="2025-10-04"),
    to_date: Optional[date] = Query(None, description="Filter orders up to this date", example="2025-11-04"),
    db: AsyncSession = Depends(get_postgresql_db),
):
    filters = []

    if user_id:
        filters.append(Order.user_id == user_id)
    if status:
        filters.append(Order.status == status)
    if from_date:
        filters.append(Order.created_at >= from_date)
    if to_date:
        filters.append(Order.created_at <= to_date)

    stmt = select(Order)
    if filters:
        stmt = (
            stmt
            .options(
                selectinload(Order.user),
                selectinload(Order.items)
            )
            .where(and_(*filters))
        )

    result = await db.execute(stmt)
    orders = result.scalars().all()

    return orders
