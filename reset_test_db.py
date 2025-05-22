import asyncio
from app.core.database import Base
from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine

async def reset():
    print(f"TEST_DATABASE_URL: {settings.TEST_DATABASE_URL}")
    engine = create_async_engine(settings.TEST_DATABASE_URL)
    async with engine.begin() as conn:
        print("Dropping all tables...")
        await conn.run_sync(Base.metadata.drop_all)
        print("Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("Test database reset complete.")

if __name__ == "__main__":
    asyncio.run(reset()) 