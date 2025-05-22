import asyncio
from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check():
    engine = create_async_engine(settings.TEST_DATABASE_URL)
    async with engine.begin() as conn:
        result = await conn.execute(text('SELECT COUNT(*) FROM "user"'))
        count = result.scalar()
        print(f'User table row count: {count}')
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check()) 