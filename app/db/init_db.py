from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
from app.core.config import settings
from app.services.user_service import create_user
from app.schemas.user import UserCreate
from app.core.security.roles import UserRole
from app.db.session import engine
from app.db.base import BaseModel
import asyncio

async def create_enum_types():
    """Create PostgreSQL enum types."""
    async with engine.begin() as conn:
        await conn.execute(text("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'userrole') THEN
                    CREATE TYPE userrole AS ENUM ('admin', 'user', 'viewer', 'editor', 'owner');
                END IF;
            END $$;
        """))
        await conn.commit()

async def main():
    print("Creating enum types...")
    await create_enum_types()
    print("Enum types created.")

    print("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
    print("Tables created.")

    # You might want to get a db session here and call init_db(db)
    # async with AsyncSession(engine) as session:
    #     await init_db(session)
    print("Initial users are typically created here after tables exist.")

if __name__ == "__main__":
    asyncio.run(main())
