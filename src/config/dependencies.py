from decimal import Decimal
from typing import Callable, Iterable
from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import stripe
from src.database.models.orders import Order, OrderItem, OrderStatus
from src.exceptions.token import TokenExpiredError, InvalidTokenError
from src.database.models.accounts import UserGroupEnum, UserModel
from src.notifications.emails import EmailSender, EmailSenderInterface
from src.config.settings import BaseAppSettings
from src.security.token_manager import JWTTokenManager
from fastapi.security import OAuth2PasswordBearer
from src.schemas.accounts import UserRetrieveSchema
from src.database.session_postgres import get_postgresql_db
from sqlalchemy.ext.asyncio import AsyncSession


def get_settings() -> BaseAppSettings:
    return BaseAppSettings()

def get_accounts_email_notificator(
    settings: BaseAppSettings = Depends(get_settings)
) -> EmailSenderInterface:

    return EmailSender(
        hostname=settings.EMAIL_HOST,
        port=settings.EMAIL_PORT,
        email=settings.EMAIL_HOST_USER,
        password=settings.EMAIL_HOST_PASSWORD,
        use_tls=settings.EMAIL_USE_TLS,
        template_dir=settings.PATH_TO_EMAIL_TEMPLATES_DIR,
        activation_email_template_name=settings.ACTIVATION_EMAIL_TEMPLATE_NAME,
        activation_email_complete_template_name=settings.ACTIVATION_EMAIL_COMPLETE_TEMPLATE_NAME,
        password_reset_email_request_template_name=settings.PASSWORD_RESET_TEMLATE_NAME,
        password_reset_email_complete_template_name=settings.PASSWORD_RESET_COMPLETE_TEMLATE_NAME,
        password_change_email_complete_template_name=settings.PASSWORD_CHANGE_COMPLETE_TEMLATE_NAME,
        successfull_payment_email_template_name=settings.SUCCESSFULL_PAYMENT_EMAIL_TEMPLATE_NAME
    )

def get_jwt_manager(
        settings: BaseAppSettings = Depends(get_settings)
) -> JWTTokenManager:
    return JWTTokenManager(
        secret_key_access=settings.SECRET_KEY_ACCESS,
        secret_key_refresh=settings.SECRET_KEY_REFRESH,
        algorithm=settings.JWT_SIGNING_ALGORITHM
    )

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_postgresql_db),
    jwt_manager: JWTTokenManager = Depends(get_jwt_manager)
) -> UserRetrieveSchema:
    try:
        payload = jwt_manager.decode_access_token(token)
        if payload is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        result = await db.execute(
            select(UserModel)
            .options(selectinload(UserModel.group))
            .options(selectinload(UserModel.region))
            .where(UserModel.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
    except (TokenExpiredError, InvalidTokenError):
        raise HTTPException(status_code=400, detail="Invalid or expired token")
        
    return UserRetrieveSchema(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
        group=UserGroupEnum(user.group.name),
        region=user.region
    )

def require_roles(roles: Iterable[str]) -> Callable:
    roles_set = {role.upper() for role in roles}
    async def checker(current_user: UserRetrieveSchema = Depends(get_current_user)):
        user_role = str(current_user.group).upper()
        if user_role not in roles_set:
            raise HTTPException(status_code=403, detail="Access forbidden")
        return current_user
    return checker


async def get_checkout_session(
    order_id: int,
    db: AsyncSession,
    user: UserRetrieveSchema,
    settings: BaseAppSettings
):
    stmt = select(Order).options(
        selectinload(Order.items).selectinload(OrderItem.movie),
        selectinload(Order.user),
    ).where(Order.id == order_id)

    result = await db.execute(stmt)
    order = result.scalars().first()

    if not order or order.user_id != user.id:
        raise HTTPException(status_code=404, detail="Order not found or access denied")
    if order.status == OrderStatus.CANCELED:
        raise HTTPException(status_code=400, detail="Order is canceled")
    if order.status == OrderStatus.PAID:
        raise HTTPException(status_code=400, detail="Order is already paid")

    try:
        stripe.api_key = settings.STRIPE_API_KEY
        list_items = []

        for item in order.items:    
            list_items.append({
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": item.movie.name
                    },
                    "unit_amount": int(item.price_at_order * 100),
                },
                "quantity": 1
            })

        session = stripe.checkout.Session.create(
            success_url="http://127.0.0.1:8000/api/v1/payment/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=f"http://127.0.0.1:8000/api/v1/orders/cancel?order_id={order.id}",
            line_items=list_items,
            mode="payment",
            metadata={
                "order_id": str(order.id),
                "user_id": str(user.id)
            },
        )

        return {"checkout_url": session.url}

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Stripe error: {e.user_message}")