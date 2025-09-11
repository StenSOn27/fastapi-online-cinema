from pydantic import BaseModel, EmailStr, field_validator
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
