from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database.models.accounts import UserModel


async def get_user_by_email(db: AsyncSession, email: str) -> UserModel | None:
    """Retrieve a user by their email address."""

    result = await db.execute(select(UserModel).where(UserModel.email == email))
    return result.scalar_one_or_none()