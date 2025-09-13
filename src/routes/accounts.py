from fastapi import APIRouter, Depends, HTTPException, Request, status, BackgroundTasks
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from src.crud import get_user_by_email
from src.schemas.accounts import UserRegisterRequestSchema
from src.database.models.accounts import ActivationTokenModel, UserGroupEnum, UserModel, UserGroupModel
from src.database.session_sqlite import get_db
from sqlalchemy import select
from src.utils import hash_password
from src.config.dependencies import get_accounts_email_notificator
from src.notifications.emails import EmailSenderInterface

router = APIRouter(prefix="/accounts")

@router.post("/register/")
async def register_user(
    request: Request,
    user_data: UserRegisterRequestSchema,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    email_sender: EmailSenderInterface = Depends(get_accounts_email_notificator),
):

    existing_user = await get_user_by_email(db, user_data.email)

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    stmt = select(UserGroupModel).filter_by(name=UserGroupEnum.USER)
    result = await db.execute(stmt)
    user_group = result.scalars().first()
    print(user_group)
    if not user_group:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Default user group not found."
        )

    hashed_password = hash_password(user_data.password)

    try:
        new_user = UserModel(
            email=user_data.email,
            _hashed_password=hashed_password,
            is_active=False,
            group=user_group
        )
        db.add(new_user)
        await db.flush()

        existing_token_result = await db.execute(
            select(ActivationTokenModel).filter_by(user_id=new_user.id)
        )
        existing_token = existing_token_result.scalars().first()
        if existing_token:
            await db.delete(existing_token)
            await db.flush()
        
        activation_token = ActivationTokenModel(user=new_user)
        db.add(activation_token)
        await db.flush()
        await db.refresh(activation_token)
        token_value = activation_token.token


        await db.commit()
        await db.refresh(new_user)

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during user creation."
        ) from e
    else:
        BASE_URL = str(request.base_url)
        activation_link = f"{BASE_URL}accounts/activate/?token={token_value}"
        background_tasks.add_task(
            email_sender.send_activation_email,
            str(user_data.email),
            activation_link
        )
        return {"message": "User registered successfully. Please check your email to activate your account.",}