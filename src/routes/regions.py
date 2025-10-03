# src/routes/regions.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database.session_sqlite import get_db
from src.database.models.regions import Region
from src.schemas.regions import RegionSchema

router = APIRouter(prefix="/regions")


@router.get("/", response_model=list[RegionSchema])
async def get_all_regions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Region))
    return result.scalars().all()
