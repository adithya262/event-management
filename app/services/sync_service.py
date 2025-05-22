from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.sync_state import SyncState
from app.models.audit_log import AuditLog
from app.core.security import generate_sync_token
from app.core.exceptions import SyncError

class SyncService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_sync_state(self, user_id: str, client_id: str, entity_type: str) -> Optional[SyncState]:
        """Get or create sync state for a client."""
        result = await self.db.execute(
            select(SyncState).where(
                SyncState.user_id == user_id,
                SyncState.client_id == client_id,
                SyncState.entity_type == entity_type,
                SyncState.is_active == True
            )
        )
        sync_state = result.scalar_one_or_none()

        if not sync_state:
            sync_state = SyncState(
                user_id=user_id,
                client_id=client_id,
                entity_type=entity_type,
                sync_token=generate_sync_token()
            )
            self.db.add(sync_state)
            await self.db.commit()
            await self.db.refresh(sync_state)

        return sync_state

    async def get_changes(
        self,
        user_id: str,
        client_id: str,
        entity_type: str,
        last_sync_version: int,
        limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], str]:
        """Get changes since last sync."""
        sync_state = await self.get_sync_state(user_id, client_id, entity_type)
        result = await self.db.execute(
            select(AuditLog)
            .where(
                AuditLog.user_id == user_id,
                AuditLog.entity_type == entity_type,
                AuditLog.timestamp > sync_state.last_sync_timestamp
            )
            .order_by(AuditLog.timestamp.asc())
            .limit(limit)
        )
        changes = result.scalars().all()

        # Update sync state
        if changes:
            sync_state.last_sync_timestamp = changes[-1].timestamp
            sync_state.last_sync_version += 1
            sync_state.sync_token = generate_sync_token()
            await self.db.commit()

        return [change.to_dict() for change in changes], sync_state.sync_token

    async def acknowledge_sync(
        self,
        user_id: str,
        client_id: str,
        entity_type: str,
        sync_token: str
    ) -> None:
        """Acknowledge successful sync."""
        sync_state = await self.get_sync_state(user_id, client_id, entity_type)

        if sync_state.sync_token != sync_token:
            raise SyncError("Invalid sync token")

        sync_state.last_sync_timestamp = datetime.utcnow()
        await self.db.commit()

    async def reset_sync_state(
        self,
        user_id: str,
        client_id: str,
        entity_type: str
    ) -> SyncState:
        """Reset sync state for a client."""
        sync_state = await self.get_sync_state(user_id, client_id, entity_type)
        sync_state.last_sync_version = 0
        sync_state.last_sync_timestamp = datetime.utcnow()
        sync_state.sync_token = generate_sync_token()
        await self.db.commit()
        return sync_state 