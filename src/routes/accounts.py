import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.database.validators import validate_password_strength
from src.security.token_manager import JWTTokenManager
from src.crud import get_user_by_email
from src.schemas.accounts import (
    ChangePasswordSchema, PasswordResetCompleteRequestSchema,
    TokenRefreshRequestSchema, TokenRefreshResponseSchema, UserLoginResponseSchema,
    UserLoginSchema, UserRegisterRequestSchema, UserResetPasswordSchema
)
from src.database.models.accounts import (
    ActivationTokenModel, UserGroupEnum,
    UserModel, UserGroupModel, PasswordResetToken, RefreshToken
)
from src.database.session_sqlite import get_db
from sqlalchemy import cast, delete, select
from src.utils import hash_password, verify_password
from src.config.dependencies import get_accounts_email_notificator, get_jwt_manager
from src.notifications.emails import EmailSenderInterface

router = APIRouter(prefix="/accounts")

oauth2_schema = OAuth2PasswordBearer(tokenUrl="login")

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


@router.post("/activate/")
async def activate_user(
    token: str, request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    email_sender: EmailSenderInterface = Depends(get_accounts_email_notificator),
):

    stmt = select(ActivationTokenModel).options(selectinload(ActivationTokenModel.user))
    result = await db.execute(stmt.filter_by(token=token))
    activation_token = result.scalars().first()
    print(activation_token)
    if not activation_token:
        raise HTTPException(status_code=400, detail="Invalid or expired activation token.")

    user = activation_token.user
    if user.is_active:
        raise HTTPException(status_code=400, detail="User account is already active.")

    try:
        user.is_active = True
        await db.delete(activation_token)
        await db.commit()
        await db.refresh(user)
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during account activation."
        ) from e
    else:
        BASE_URL = str(request.base_url)
        login_link = f"{BASE_URL}accounts/login/"
        background_tasks.add_task(
            email_sender.send_activation_complete_email,
            str(user.email),
            login_link
        )
        return {"message": "Account activated successfully."}


@router.post("/change-password")
async def change_password(
    request: Request,
    data: ChangePasswordSchema,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    email_sender: EmailSenderInterface = Depends(get_accounts_email_notificator)
):
    user = await get_user_by_email(db, data.email)
    if not verify_password(data.old_password, user._hashed_password):
        raise HTTPException(status_code=400, detail="Wrong old password")
    try:
        validate_password_strength(data.new_password)
        user._hashed_password = hash_password(data.new_password)
        await db.commit()
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during account activation."
        ) from e
    else:
        BASE_URL = str(request.base_url)
        login_link = f"{BASE_URL}accounts/login/"
        background_tasks.add_task(
            email_sender.send_password_change_complete_email,
            str(data.email),
            login_link
        )
        return {"message": "Password changed"}


@router.post("/reset-password/request/")
async def reset_password_request(
    request: Request,
    background_tasks: BackgroundTasks,
    user_data: UserResetPasswordSchema,
    db: AsyncSession = Depends(get_db),
    email_sender: EmailSenderInterface = Depends(get_accounts_email_notificator),
):
    user = await get_user_by_email(db, user_data.email)
    if not user:
        raise HTTPException(status_code=400, detail="User is not registered")

    await db.execute(delete(PasswordResetToken).where(PasswordResetToken.user_id == user.id))

    reset_token = PasswordResetToken(user_id=user.id)
    db.add(reset_token)
    await db.commit()
    BASE_URL = str(request.base_url)
    reset_password_link = f"{BASE_URL}accounts/reset-password/complete/?token={reset_token.token}"

    background_tasks.add_task(
        email_sender.send_password_reset_email,
        str(user_data.email),
        reset_password_link
    )
    return {"message": "If you are registered, you will receive an email with instructions."}


@router.post("/reset-password/complete/")
async def reset_password(
    request: Request,
    user_data: PasswordResetCompleteRequestSchema,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    email_sender: EmailSenderInterface = Depends(get_accounts_email_notificator),
) -> dict:

    stmt = select(PasswordResetToken).options(selectinload(PasswordResetToken.user))
    result = await db.execute(stmt.filter_by(token=user_data.token))
    reset_password_token = result.scalars().first()

    if not reset_password_token:
        raise HTTPException(status_code=400, detail="Invalid or expired activation token.")

    user = reset_password_token.user
    if not user:
        raise HTTPException(status_code=400, detail="User is not registered.")

    try:
        user._hashed_password = hash_password(user_data.new_password)
        await db.delete(reset_password_token)
        await db.commit()
        await db.refresh(user)
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during account activation."
        ) from e
    else:
        BASE_URL = str(request.base_url)
        login_link = f"{BASE_URL}accounts/login/"
        background_tasks.add_task(
            email_sender.send_password_reset_complete_email,
            str(user.email),
            login_link
        )
        return {"message": "Account activated successfully."}


@router.post("/login/")
async def login_user(
        login_data: UserLoginSchema,
        db: AsyncSession = Depends(get_db),
        jwt_manager: JWTTokenManager = Depends(get_jwt_manager),
) -> UserLoginResponseSchema:

    user = await get_user_by_email(db, login_data.email)

    if not user or not verify_password(login_data.password, user._hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not activated.",
        )

    jwt_refresh_token = jwt_manager.create_refresh_token({"user_id": user.id})

    try:
        refresh_token = RefreshToken(
            user_id = user.id,
            expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1),
            token=jwt_refresh_token
        )
        db.add(refresh_token)
        await db.flush()
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the request.",
        )

    jwt_access_token = jwt_manager.create_access_token({"user_id": user.id})
    return UserLoginResponseSchema(
        access_token=jwt_access_token,
        refresh_token=jwt_refresh_token,
    )


@router.post("/refresh/", response_model=TokenRefreshResponseSchema)
async def refresh_access_token(
        token_data: TokenRefreshRequestSchema,
        db: AsyncSession = Depends(get_db),
        jwt_manager: JWTTokenManager = Depends(get_jwt_manager),
) -> TokenRefreshResponseSchema:

    decoded_token = jwt_manager.decode_refresh_token(token_data.token)
    print(decoded_token)
    user_id = decoded_token.get("user_id")

    stmt = select(RefreshToken).filter_by(token=token_data.token)
    result = await db.execute(stmt)
    refresh_token_record = result.scalars().first()
    if not refresh_token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found.",
        )

    stmt = select(UserModel).filter_by(id=user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    new_access_token = jwt_manager.create_access_token({"user_id": user_id})

    return TokenRefreshResponseSchema(access_token=new_access_token)
