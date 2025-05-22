from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.version import Version
import logging

logger = logging.getLogger(__name__)

class ConflictResolutionStrategy:
    """Base class for conflict resolution strategies."""
    
    def resolve(self, current_state: Dict[str, Any], incoming_changes: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve conflicts between current state and incoming changes."""
        raise NotImplementedError

class LastWriteWinsStrategy(ConflictResolutionStrategy):
    """Strategy that always takes the most recent changes."""
    
    def resolve(self, current_state: Dict[str, Any], incoming_changes: Dict[str, Any]) -> Dict[str, Any]:
        return incoming_changes

class ManualResolutionStrategy(ConflictResolutionStrategy):
    """Strategy that requires manual resolution of conflicts."""
    
    def resolve(self, current_state: Dict[str, Any], incoming_changes: Dict[str, Any]) -> Dict[str, Any]:
        conflicts = self._find_conflicts(current_state, incoming_changes)
        if conflicts:
            raise ConflictResolutionRequired(conflicts)
        return incoming_changes
    
    def _find_conflicts(self, current_state: Dict[str, Any], incoming_changes: Dict[str, Any]) -> List[Dict[str, Any]]:
        conflicts = []
        for key in set(current_state.keys()) & set(incoming_changes.keys()):
            if current_state[key] != incoming_changes[key]:
                conflicts.append({
                    "field": key,
                    "current_value": current_state[key],
                    "incoming_value": incoming_changes[key]
                })
        return conflicts

class MergeStrategy(ConflictResolutionStrategy):
    """Strategy that attempts to merge changes intelligently."""
    
    def resolve(self, current_state: Dict[str, Any], incoming_changes: Dict[str, Any]) -> Dict[str, Any]:
        merged_state = current_state.copy()
        
        for key, value in incoming_changes.items():
            if key not in current_state:
                merged_state[key] = value
            elif isinstance(value, dict) and isinstance(current_state[key], dict):
                merged_state[key] = self.resolve(current_state[key], value)
            elif isinstance(value, list) and isinstance(current_state[key], list):
                merged_state[key] = self._merge_lists(current_state[key], value)
            else:
                # For simple values, take the incoming change
                merged_state[key] = value
        
        return merged_state
    
    def _merge_lists(self, current_list: List[Any], incoming_list: List[Any]) -> List[Any]:
        """Merge two lists, preserving order and handling duplicates."""
        result = current_list.copy()
        for item in incoming_list:
            if item not in result:
                result.append(item)
        return result

class ConflictResolutionRequired(Exception):
    """Exception raised when manual conflict resolution is required."""
    
    def __init__(self, conflicts: List[Dict[str, Any]]):
        self.conflicts = conflicts
        super().__init__("Manual conflict resolution required")

class ConflictResolver:
    """Main class for handling conflict resolution."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.strategies = {
            "last_write_wins": LastWriteWinsStrategy(),
            "manual": ManualResolutionStrategy(),
            "merge": MergeStrategy()
        }
    
    async def resolve_conflicts(
        self,
        entity_type: str,
        entity_id: str,
        incoming_changes: Dict[str, Any],
        strategy: str = "merge"
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Resolve conflicts between current state and incoming changes."""
        # Get current state
        current_state = await self._get_current_state(entity_type, entity_id)
        
        # Get resolution strategy
        resolution_strategy = self.strategies.get(strategy)
        if not resolution_strategy:
            raise ValueError(f"Unknown conflict resolution strategy: {strategy}")
        
        try:
            # Attempt to resolve conflicts
            resolved_state = resolution_strategy.resolve(current_state, incoming_changes)
            
            # Create version record
            version = Version(
                entity_type=entity_type,
                entity_id=entity_id,
                version_number=await self._get_next_version_number(entity_type, entity_id),
                changes=incoming_changes,
                previous_state=current_state,
                current_state=resolved_state,
                created_by="system"  # This should be replaced with actual user ID
            )
            
            self.session.add(version)
            await self.session.commit()
            
            return resolved_state, []
            
        except ConflictResolutionRequired as e:
            return current_state, e.conflicts
    
    async def _get_current_state(self, entity_type: str, entity_id: str) -> Dict[str, Any]:
        """Get the current state of an entity."""
        # This should be implemented based on your entity types
        # For now, we'll return an empty dict
        return {}
    
    async def _get_next_version_number(self, entity_type: str, entity_id: str) -> int:
        """Get the next version number for an entity."""
        latest_version = await self.session.query(Version)\
            .filter(Version.entity_type == entity_type)\
            .filter(Version.entity_id == entity_id)\
            .order_by(Version.version_number.desc())\
            .first()
        
        return (latest_version.version_number + 1) if latest_version else 1 