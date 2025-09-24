from typing import Annotated
from pydantic import BaseModel, EmailStr, StringConstraints, field_validator
from src.database.validators import validate_password_strength, validate_email_address


class BaseEmailPasswordSchema(BaseModel):
    email: EmailStr
    password: str

    model_config = {
        "from_attributes": True
    }

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        return validate_email_address(value)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        return validate_password_strength(value)


class UserRegisterRequestSchema(BaseEmailPasswordSchema):
    pass


class UserResetPasswordSchema(BaseModel):
    email: EmailStr


class ChangePasswordSchema(BaseModel):
    email: EmailStr
    old_password: str
    new_password:Annotated[
                    str,
                    StringConstraints(min_length=8)
                ]


class PasswordResetCompleteRequestSchema(BaseModel):
    token: str
    new_password: str

class UserLoginSchema(BaseEmailPasswordSchema):
    pass


class TokenRefreshRequestSchema(BaseEmailPasswordSchema):
    token: str


class UserLoginResponseSchema(BaseModel):
    access_token: str
    refresh_token: str


class TokenRefreshResponseSchema(BaseModel):
    access_token: str
