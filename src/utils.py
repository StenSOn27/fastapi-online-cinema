from passlib.context import CryptContext
import secrets

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)


def generate_secure_token(length: int = 32) -> str:
    return secrets.token_urlsafe(length)
