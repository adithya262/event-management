from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api import deps
from app.services.sync_service import SyncService
from app.core.exceptions import SyncError

router = APIRouter()

@router.get("/changes")
async def get_changes(
    entity_type: str,
    client_id: str,
    last_sync_version: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
) -> Dict[str, Any]:
    """Get changes since last sync."""
    sync_service = SyncService(db)
    try:
        changes, sync_token = sync_service.get_changes(
            user_id=current_user.id,
            client_id=client_id,
            entity_type=entity_type,
            last_sync_version=last_sync_version,
            limit=limit
        )
        return {
            "changes": changes,
            "sync_token": sync_token,
            "has_more": len(changes) == limit
        }
    except SyncError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/acknowledge")
async def acknowledge_sync(
    entity_type: str,
    client_id: str,
    sync_token: str,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
) -> Dict[str, str]:
    """Acknowledge successful sync."""
    sync_service = SyncService(db)
    try:
        sync_service.acknowledge_sync(
            user_id=current_user.id,
            client_id=client_id,
            entity_type=entity_type,
            sync_token=sync_token
        )
        return {"status": "success"}
    except SyncError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reset")
async def reset_sync(
    entity_type: str,
    client_id: str,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
) -> Dict[str, Any]:
    """Reset sync state for a client."""
    sync_service = SyncService(db)
    sync_state = sync_service.reset_sync_state(
        user_id=current_user.id,
        client_id=client_id,
        entity_type=entity_type
    )
    return sync_state.to_dict() 