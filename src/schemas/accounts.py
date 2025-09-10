from pydantic import BaseModel, EmailStr, field_validator
from database.validators import validate_password_strength, email_validation


class BaseEmailPasswordSchema(BaseModel):
    email: EmailStr
    password: str

    model_config = {
        "from_attributes": True
    }

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        return email_validation(value)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        return validate_password_strength(value)


class UserRegisterRequestSchema(BaseEmailPasswordSchema):
    pass
