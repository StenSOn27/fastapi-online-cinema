import asyncio
import asyncpg
from src.config.settings_instance import get_settings

settings = get_settings()

async def wait_for_db():
    while True:
        try:
            conn = await asyncpg.connect(
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                database=settings.POSTGRES_DB,
                host=settings.POSTGRES_HOST,
                port=settings.POSTGRES_PORT,
            )
            await conn.close()
            print("✅ Database is ready!")
            break
        except Exception:
            print("⏳ Waiting for database...")
            await asyncio.sleep(0.5)

asyncio.run(wait_for_db())
