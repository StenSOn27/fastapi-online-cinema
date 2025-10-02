from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from src.schemas.movies import StarSchema
from src.database.models.movies import Star
from src.config.dependencies import get_db, require_roles


router = APIRouter(prefix="/movies/stars")

@router.post("/", response_model=StarSchema, dependencies=[Depends(require_roles(["moderator"]))])
async def create_star(name: str, db: AsyncSession = Depends(get_db)):
    star = Star(name=name)
    db.add(star)
    try:
        await db.commit()
        await db.refresh(star)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Star already exists")

    return star


@router.put("/{star_id}/", response_model=StarSchema, dependencies=[Depends(require_roles(["moderator"]))])
async def update_star(star_id: int, name: str, db: AsyncSession = Depends(get_db)):
    star = await db.get(Star, star_id)
    if not star:
        raise HTTPException(status_code=404, detail="Star not found")

    star.name = name
    try:
        await db.commit()
        await db.refresh(star)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Failed to update star")

    return star

@router.delete("/{star_id}/", status_code=204, dependencies=[Depends(require_roles(["moderator"]))])
async def delete_star(star_id: int, db: AsyncSession = Depends(get_db)):
    star = await db.get(Star, star_id)
    if not star:
        raise HTTPException(status_code=404, detail="Star not found")

    await db.delete(star)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Cannot delete star (possibly in use)")
