from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy.sql import text
from app.core.config import settings
import logging
import backoff
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

# Create async engine with optimized settings
engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=settings.DB_ECHO,
    future=True,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,  # Enable connection health checks
    connect_args={
        "command_timeout": settings.DB_COMMAND_TIMEOUT,
        "server_settings": {
            "application_name": settings.PROJECT_NAME,
            "statement_timeout": str(settings.DB_STATEMENT_TIMEOUT),
            "idle_in_transaction_session_timeout": str(settings.DB_IDLE_TIMEOUT)
        }
    }
)

# Create async session factory with optimized settings
async_session_factory = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

class Base(DeclarativeBase):
    """Base class for all database models."""
    pass

@backoff.on_exception(
    backoff.expo,
    (OperationalError, SQLAlchemyError),
    max_tries=3,
    max_time=30
)
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Database error occurred: {str(e)}")
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Unexpected error occurred: {str(e)}")
            raise
        finally:
            await session.close()

@asynccontextmanager
async def get_db_context():
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()

@backoff.on_exception(
    backoff.expo,
    (OperationalError, SQLAlchemyError),
    max_tries=3,
    max_time=30
)
async def init_db() -> None:
    """Initialize database connection and verify connectivity with retry logic."""
    try:
        async with engine.begin() as conn:
            # Test connection
            await conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            
            # Get database version
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"Connected to PostgreSQL version: {version}")
            
            # Get database statistics
            stats = await conn.execute(text("""
                SELECT
                    datname,
                    numbackends,
                    xact_commit,
                    xact_rollback,
                    blks_read,
                    blks_hit,
                    tup_returned,
                    tup_fetched,
                    tup_inserted,
                    tup_updated,
                    tup_deleted
                FROM pg_stat_database
                WHERE datname = current_database()
            """))
            db_stats = stats.first()
            if db_stats:
                stats_dict = {
                    'datname': db_stats[0],
                    'numbackends': db_stats[1],
                    'xact_commit': db_stats[2],
                    'xact_rollback': db_stats[3],
                    'blks_read': db_stats[4],
                    'blks_hit': db_stats[5],
                    'tup_returned': db_stats[6],
                    'tup_fetched': db_stats[7],
                    'tup_inserted': db_stats[8],
                    'tup_updated': db_stats[9],
                    'tup_deleted': db_stats[10]
                }
                logger.info(f"Database statistics: {stats_dict}")
            
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise 