from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.accounts import UserRegisterRequestSchema
from src.database.models.accounts import ActivationTokenModel, UserGroupEnum, UserModel, UserGroupModel
from src.database.session_sqlite import get_db
from sqlalchemy import select
from src.utils import hash_password


router = APIRouter()

@router.post("register/")
async def register_user(
    user_data: UserRegisterRequestSchema,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(UserModel).where(email=user_data.email))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    default_group = await db.execute(
        select(UserGroupModel)
        .filter_by(name=UserGroupEnum.USER)
    ).scalars().first()

    hashed_password = hash_password(user_data.password)

    new_user = UserModel(
        email=user_data.email,
        _hashed_password=hashed_password,
        is_active=False,
        group=default_group
    )

    activation_token = ActivationTokenModel(user=new_user)

    await db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return {
        "message": "Created succesfully, your account is inactive, to activate use activation token",
        "activation token": activation_token.token
    }
