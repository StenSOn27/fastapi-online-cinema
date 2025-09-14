import os
from pathlib import Path
from pydantic_settings import BaseSettings


class BaseAppSettings(BaseSettings):
    BASE_DIR: Path = Path(__file__).parent.parent

    PATH_TO_EMAIL_TEMPLATES_DIR: str = str(BASE_DIR / "notifications" / "templates")
    ACTIVATION_EMAIL_TEMPLATE_NAME: str = "activation_request.html"
    ACTIVATION_EMAIL_COMPLETE_TEMPLATE_NAME: str = "activation_complete.html"
    PASSWORD_RESET_TEMLATE_NAME: str = "password_reset_request.html"
    PASSWORD_RESET_COMPLETE_TEMLATE_NAME: str = "password_reset_complete.html"
    PASSWORD_CHANGE_COMPLETE_TEMLATE_NAME: str = "password_change_complete.html"

    EMAIL_HOST: str = os.getenv("EMAIL_HOST", "localhost")
    EMAIL_PORT: int = int(os.getenv("EMAIL_PORT", 1025))
    EMAIL_HOST_USER: str = os.getenv("EMAIL_HOST_USER", "testuser")
    EMAIL_HOST_PASSWORD: str = os.getenv("EMAIL_HOST_PASSWORD", "test_password")
    EMAIL_USE_TLS: bool = os.getenv("EMAIL_USE_TLS", "False").lower() == "true"
    MAILHOG_API_PORT: int = os.getenv("MAILHOG_API_PORT", 8025)

    SECRET_KEY_ACCESS: str = os.getenv("SECRET_KEY_ACCESS", str(os.urandom(32)))
    SECRET_KEY_REFRESH: str = os.getenv("SECRET_KEY_REFRESH", str(os.urandom(32)))
    JWT_SIGNING_ALGORITHM: str = os.getenv("JWT_SIGNING_ALGORITHM", "HS256")
