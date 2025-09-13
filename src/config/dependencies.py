from fastapi import Depends
from src.notifications.emails import EmailSender, EmailSenderInterface
from src.config.settings import BaseAppSettings
from src.security.token_manager import JWTTokenManager


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
        activation_email_complete_template_name=settings.ACTIVATION_EMAIL_COMPLETE_TEMPLATE_NAME
    )

def get_jwt_manager(
        settings: BaseAppSettings = Depends(get_settings)
) -> JWTTokenManager:
    return JWTTokenManager(
        secret_key_access=settings.SECRET_KEY_ACCESS,
        secret_key_refresh=settings.SECRET_KEY_REFRESH,
        algorithm=settings.JWT_SIGNING_ALGORITHM
    )