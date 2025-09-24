from fastapi import Depends, HTTPException
from sqlalchemy import select
from src.database.models.accounts import UserModel
from src.notifications.emails import EmailSender, EmailSenderInterface
from src.config.settings import BaseAppSettings
from src.security.token_manager import JWTTokenManager
from fastapi.security import OAuth2PasswordBearer
from src.schemas.accounts import UserRetrieveSchema
from src.database.session_sqlite import get_db
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
    db: AsyncSession = Depends(get_db),
    jwt_manager: JWTTokenManager = Depends(get_jwt_manager)
) -> UserRetrieveSchema:
    payload = jwt_manager.decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    db_user = await db.execute(select(UserModel).where(UserModel.id == user_id))
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserRetrieveSchema.model_validate(db_user)

async def require_admin(current_user: UserRetrieveSchema = Depends(get_current_user)):
    if current_user.group_id != 3:
        raise HTTPException(status_code=403, detail="Access forbidden: admins only")
    return current_user
