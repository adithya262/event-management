from typing import Any, Dict, List, Optional, Type, TypeVar
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, NoResultFound
import logging
from app.core.exceptions import (
    DatabaseException,
    NotFoundException,
    ConflictException,
    ValidationException
)

logger = logging.getLogger(__name__)

T = TypeVar('T')

class DatabaseUtils:
    @staticmethod
    async def get_by_id(
        session: AsyncSession,
        model: Type[T],
        id: str,
        load_relationships: bool = False
    ) -> Optional[T]:
        """Get a record by ID with optional relationship loading."""
        try:
            query = select(model).where(model.id == id)
            
            if load_relationships:
                # Load all relationships using selectinload
                for relationship in model.__mapper__.relationships:
                    query = query.options(selectinload(relationship.key))
            
            result = await session.execute(query)
            instance = result.scalar_one_or_none()
            
            if not instance:
                raise NotFoundException(
                    message=f"{model.__name__} with id {id} not found",
                    details={"model": model.__name__, "id": id}
                )
            
            return instance
            
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching {model.__name__}: {str(e)}")
            raise DatabaseException(
                message=f"Error fetching {model.__name__}",
                details={"error": str(e)}
            )

    @staticmethod
    async def get_all(
        session: AsyncSession,
        model: Type[T],
        skip: int = 0,
        limit: int = 100,
        load_relationships: bool = False
    ) -> List[T]:
        """Get all records with pagination and optional relationship loading."""
        try:
            query = select(model).offset(skip).limit(limit)
            
            if load_relationships:
                # Load all relationships using selectinload
                for relationship in model.__mapper__.relationships:
                    query = query.options(selectinload(relationship.key))
            
            result = await session.execute(query)
            return result.scalars().all()
            
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching all {model.__name__}: {str(e)}")
            raise DatabaseException(
                message=f"Error fetching {model.__name__} list",
                details={"error": str(e)}
            )

    @staticmethod
    async def create(
        session: AsyncSession,
        model: Type[T],
        data: Dict[str, Any]
    ) -> T:
        """Create a new record."""
        try:
            instance = model(**data)
            session.add(instance)
            await session.commit()
            await session.refresh(instance)
            return instance
            
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"Integrity error while creating {model.__name__}: {str(e)}")
            raise ConflictException(
                message=f"Error creating {model.__name__}",
                details={"error": str(e)}
            )
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Database error while creating {model.__name__}: {str(e)}")
            raise DatabaseException(
                message=f"Error creating {model.__name__}",
                details={"error": str(e)}
            )

    @staticmethod
    async def update(
        session: AsyncSession,
        model: Type[T],
        id: str,
        data: Dict[str, Any]
    ) -> Optional[T]:
        """Update a record by ID."""
        try:
            # Check if record exists
            instance = await DatabaseUtils.get_by_id(session, model, id)
            if not instance:
                raise NotFoundException(
                    message=f"{model.__name__} with id {id} not found",
                    details={"model": model.__name__, "id": id}
                )

            query = (
                update(model)
                .where(model.id == id)
                .values(**data)
                .execution_options(synchronize_session="fetch")
            )
            await session.execute(query)
            await session.commit()
            
            # Fetch updated record
            return await DatabaseUtils.get_by_id(session, model, id)
            
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"Integrity error while updating {model.__name__}: {str(e)}")
            raise ConflictException(
                message=f"Error updating {model.__name__}",
                details={"error": str(e)}
            )
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Database error while updating {model.__name__}: {str(e)}")
            raise DatabaseException(
                message=f"Error updating {model.__name__}",
                details={"error": str(e)}
            )

    @staticmethod
    async def delete(
        session: AsyncSession,
        model: Type[T],
        id: str
    ) -> bool:
        """Delete a record by ID."""
        try:
            # Check if record exists
            instance = await DatabaseUtils.get_by_id(session, model, id)
            if not instance:
                raise NotFoundException(
                    message=f"{model.__name__} with id {id} not found",
                    details={"model": model.__name__, "id": id}
                )

            query = delete(model).where(model.id == id)
            result = await session.execute(query)
            await session.commit()
            return result.rowcount > 0
            
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Database error while deleting {model.__name__}: {str(e)}")
            raise DatabaseException(
                message=f"Error deleting {model.__name__}",
                details={"error": str(e)}
            )

    @staticmethod
    async def execute_raw_query(
        session: AsyncSession,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute a raw SQL query with parameters."""
        try:
            result = await session.execute(text(query), params or {})
            return [dict(row) for row in result]
        except SQLAlchemyError as e:
            logger.error(f"Database error executing raw query: {str(e)}")
            raise DatabaseException(
                message="Error executing database query",
                details={"error": str(e), "query": query}
            )

    @staticmethod
    async def bulk_create(
        session: AsyncSession,
        model: Type[T],
        data_list: List[Dict[str, Any]]
    ) -> List[T]:
        """Bulk create records."""
        try:
            instances = [model(**data) for data in data_list]
            session.add_all(instances)
            await session.commit()
            for instance in instances:
                await session.refresh(instance)
            return instances
            
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"Integrity error during bulk create of {model.__name__}: {str(e)}")
            raise ConflictException(
                message=f"Error bulk creating {model.__name__}",
                details={"error": str(e)}
            )
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Database error during bulk create of {model.__name__}: {str(e)}")
            raise DatabaseException(
                message=f"Error bulk creating {model.__name__}",
                details={"error": str(e)}
            )

    @staticmethod
    async def bulk_update(
        session: AsyncSession,
        model: Type[T],
        data_list: List[Dict[str, Any]],
        id_field: str = "id"
    ) -> List[T]:
        """Bulk update records."""
        try:
            for data in data_list:
                id_value = data.pop(id_field)
                query = (
                    update(model)
                    .where(getattr(model, id_field) == id_value)
                    .values(**data)
                )
                await session.execute(query)
            await session.commit()
            return await DatabaseUtils.get_all(
                session,
                model,
                load_relationships=True
            )
            
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"Integrity error during bulk update of {model.__name__}: {str(e)}")
            raise ConflictException(
                message=f"Error bulk updating {model.__name__}",
                details={"error": str(e)}
            )
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Database error during bulk update of {model.__name__}: {str(e)}")
            raise DatabaseException(
                message=f"Error bulk updating {model.__name__}",
                details={"error": str(e)}
            ) 