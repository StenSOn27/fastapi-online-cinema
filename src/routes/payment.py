from decimal import Decimal
import stripe
from src.notifications.interfaces import EmailSenderInterface
from src.config.settings import BaseAppSettings
from src.database.models.orders import Order, OrderStatus
from src.schemas.payment import PaymentHistoryItem, PaymentHistoryResponse, PaymentResponseSchema, PaymentStatusEnum
from src.config.dependencies import get_accounts_email_notificator, get_current_user, get_settings
from src.database.session_sqlite import get_db
from src.schemas.accounts import UserRetrieveSchema
from src.database.models.payment import Payment, PaymentItem
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/payment")

@router.post("/success/", response_model=PaymentResponseSchema)
async def success_payment(
    background_tasks: BackgroundTasks,
    session_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    user: UserRetrieveSchema = Depends(get_current_user),
    email_sender: EmailSenderInterface = Depends(get_accounts_email_notificator),
    settings: BaseAppSettings = Depends(get_settings)
) -> PaymentResponseSchema:
    try:
        stripe.api_key = settings.STRIPE_API_KEY
        session = stripe.checkout.Session.retrieve(session_id)
        order_id = int(session.metadata.get("order_id"))

        stmt = (
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order_id)
        )
        result = await db.execute(stmt)
        order = result.scalars().first()

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.user_id != user.id:
            raise HTTPException(status_code=403, detail="Access denied: not your order")

        if order.status == OrderStatus.PAID:
            existing_payment_stmt = select(Payment).where(Payment.order_id == order.id)
            existing_result = await db.execute(existing_payment_stmt)
            existing_payment = existing_result.scalars().first()

            if existing_payment:
                return PaymentResponseSchema.model_validate(existing_payment)

            raise HTTPException(status_code=409, detail="Order marked as PAID, but payment not found")

        total_amount = sum([item.price_at_order for item in order.items])

        payment = Payment(
            user_id=user.id,
            order_id=order.id,
            amount=Decimal(total_amount),
            status=PaymentStatusEnum.SUCCESSFUL,
            external_payment_id=session.id,
        )
        db.add(payment)
        await db.flush()

        for order_item in order.items:
            payment_item = PaymentItem(
                payment_id=payment.id,
                order_item_id=order_item.id,
                price_at_payment=Decimal(order_item.price_at_order)
            )
            db.add(payment_item)

        order.status = OrderStatus.PAID
        await db.commit()
        await db.refresh(payment)

        stmt = (
            select(Payment)
            .options(selectinload(Payment.items))
            .where(Payment.id == payment.id)
        )
        result = await db.execute(stmt)
        payment_with_items = result.scalars().first()

        background_tasks.add_task(
            email_sender.send_successfull_payment_email,
            str(user.email),
            order.id
        )
        return PaymentResponseSchema.model_validate(payment_with_items)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Payment verification failed: {str(e)}")


@router.get("/history/", response_model=PaymentHistoryResponse)
async def payment_history(
    db: AsyncSession = Depends(get_db),
    user: UserRetrieveSchema = Depends(get_current_user)
):
    stmt = (
        select(Payment)
        .options(selectinload(Payment.items))
        .where(Payment.user_id == user.id)
        .order_by(Payment.created_at.desc())
    )
    result = await db.execute(stmt)
    payments = result.scalars().all()

    payments_data = [
        PaymentHistoryItem(
            created_at=payment.created_at,
            amount=float(payment.amount),
            status=payment.status
        )
        for payment in payments
    ]

    return PaymentHistoryResponse(payments=payments_data)
