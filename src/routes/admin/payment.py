from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from datetime import date
from typing import List, Optional

from src.schemas.payment import PaymentAdminResponse, PaymentResponseSchema
from src.database.models.payment import Payment, PaymentStatus

from src.database.session_sqlite import get_db
from src.config.dependencies import require_roles

router = APIRouter(prefix="/admin/payments")

@router.get(
        "/",
        response_model=PaymentAdminResponse,
        dependencies=[Depends(require_roles(["ADMIN"]))]
)
async def admin_payments_list(
    user_ids: Optional[List[int]] = Query(None, description="Filter by user IDs"),
    date_from: date = Query(None, description="Filter payments from this date"),
    date_to: date = Query(None, description="Filter payments up to this date"),
    statuses: Optional[List[PaymentStatus]] = Query(None, description="Filter by payment statuses"),
    db: AsyncSession = Depends(get_db),
):
    query = select(Payment).options(selectinload(Payment.items))

    filters = []

    if user_ids:
        filters.append(Payment.user_id.in_(user_ids))

    if date_from:
        filters.append(Payment.created_at >= date_from)

    if date_to:
        filters.append(Payment.created_at <= date_to)

    if statuses:
        filters.append(Payment.status.in_(statuses))

    if filters:
        query = query.where(and_(*filters))

    query = query.order_by(Payment.created_at.desc())

    result = await db.execute(query)
    payments = result.scalars().all()

    return PaymentAdminResponse(
        payments=[PaymentResponseSchema.model_validate(p) for p in payments]
    )
