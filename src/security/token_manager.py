import datetime
from jose import jwt, JWTError, ExpiredSignatureError
from src.exceptions.token import TokenExpiredError, InvalidTokenError


class JWTTokenManager:
    def __init__(
            self, secret_key_access: str,
            secret_key_refresh: str, algorithm: str
    ) -> None:
        self._secret_key_access = secret_key_access
        self._secret_key_refresh = secret_key_refresh
        self._algorithm = algorithm

    def _create_token(
        self, data: dict,
        secret_key: str,
        expires_delta: datetime.timedelta = None,
        algorithm: str = None
    ) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
        else:
            expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
        return encoded_jwt

    def create_access_token(self, data: dict) -> str:
        return self._create_token(
            data, self._secret_key_access,
            algorithm=self._algorithm
        )

    def create_refresh_token(self, data: dict) -> str:
        return self._create_token(
            data, self._secret_key_refresh,
            algorithm=self._algorithm
        )

    def decode_token(
            self,
            token: str,
            secret_key: str,
            algorithm: str = None
    ) -> dict:
        try:
            return jwt.decode(token, secret_key, algorithms=[algorithm])
        except ExpiredSignatureError:
            raise TokenExpiredError
        except JWTError:
            raise InvalidTokenError

    def decode_refresh_token(self, token: str):
        return self.decode_token(
            token,
            self._secret_key_refresh,
            self._algorithm
        )

    def decode_access_token(self, token: str):
        return self.decode_token(
            token,
            self._secret_key_access,
            self._algorithm
        )
