from typing import Any, Callable, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Transaction:
    """Transaction system for handling atomic operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.operations: List[Dict[str, Any]] = []
        self.rollback_operations: List[Callable] = []
        self.start_time = datetime.utcnow()
    
    async def add_operation(
        self,
        operation_type: str,
        entity_type: str,
        entity_id: str,
        data: Dict[str, Any],
        rollback_func: Optional[Callable] = None
    ):
        """Add an operation to the transaction."""
        operation = {
            "type": operation_type,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "data": data,
            "timestamp": datetime.utcnow()
        }
        self.operations.append(operation)
        if rollback_func:
            self.rollback_operations.append(rollback_func)
    
    async def commit(self):
        """Commit all operations in the transaction."""
        try:
            await self.session.commit()
            logger.info(f"Transaction committed successfully with {len(self.operations)} operations")
            return True
        except Exception as e:
            logger.error(f"Error committing transaction: {str(e)}")
            await self.rollback()
            return False
    
    async def rollback(self):
        """Rollback all operations in the transaction."""
        try:
            # Execute rollback operations in reverse order
            for rollback_func in reversed(self.rollback_operations):
                await rollback_func()
            
            await self.session.rollback()
            logger.info("Transaction rolled back successfully")
            return True
        except Exception as e:
            logger.error(f"Error rolling back transaction: {str(e)}")
            return False
    
    def get_operations(self) -> List[Dict[str, Any]]:
        """Get all operations in the transaction."""
        return self.operations

@asynccontextmanager
async def transaction_scope(session: AsyncSession):
    """Context manager for transaction scope."""
    transaction = Transaction(session)
    try:
        yield transaction
        await transaction.commit()
    except Exception as e:
        await transaction.rollback()
        raise e 