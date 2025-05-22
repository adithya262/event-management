from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.version import Version
import json
from difflib import unified_diff
import logging
from sqlalchemy import select

logger = logging.getLogger(__name__)

class ChangelogService:
    """Service for managing and visualizing changelogs."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_entity_changelog(
        self,
        entity_type: str,
        entity_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get changelog for a specific entity."""
        stmt = select(Version).filter(Version.entity_type == entity_type, Version.entity_id == entity_id)
        if start_date:
            stmt = stmt.filter(Version.created_at >= start_date)
        if end_date:
            stmt = stmt.filter(Version.created_at <= end_date)
        stmt = stmt.order_by(Version.version_number.asc())
        result = await self.session.execute(stmt)
        versions = result.scalars().all()
        return [version.to_dict() for version in versions]
    
    async def get_changes_between_versions(
        self,
        entity_type: str,
        entity_id: str,
        from_version: int,
        to_version: int
    ) -> Dict[str, Any]:
        """Get changes between two specific versions."""
        if from_version >= to_version:
            raise ValueError("from_version must be less than to_version")

        stmt_from = select(Version).filter(
            Version.entity_type == entity_type,
            Version.entity_id == entity_id,
            Version.version_number == from_version
        )
        result_from = await self.session.execute(stmt_from)
        from_version_obj = result_from.scalars().first()

        stmt_to = select(Version).filter(
            Version.entity_type == entity_type,
            Version.entity_id == entity_id,
            Version.version_number == to_version
        )
        result_to = await self.session.execute(stmt_to)
        to_version_obj = result_to.scalars().first()

        if not from_version_obj or not to_version_obj:
            raise ValueError("One or both versions not found")
        
        return {
            "from_version": from_version_obj.to_dict(),
            "to_version": to_version_obj.to_dict(),
            "changes": self._calculate_changes(
                from_version_obj.current_state,
                to_version_obj.current_state
            )
        }
    
    def _calculate_changes(self, from_state: Dict[str, Any], to_state: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate changes between two states."""
        changes = {}
        
        # Find added and modified fields
        for key in set(to_state.keys()):
            if key not in from_state:
                changes[key] = {
                    "type": "added",
                    "value": to_state[key]
                }
            elif from_state[key] != to_state[key]:
                changes[key] = {
                    "type": "modified",
                    "old_value": from_state[key],
                    "new_value": to_state[key]
                }
        
        # Find removed fields
        for key in set(from_state.keys()) - set(to_state.keys()):
            changes[key] = {
                "type": "removed",
                "value": from_state[key]
            }
        
        return changes
    
    def generate_unified_diff(
        self,
        from_state: Dict[str, Any],
        to_state: Dict[str, Any],
        context_lines: int = 3
    ) -> str:
        """Generate a unified diff between two states."""
        from_lines = json.dumps(from_state, indent=2).splitlines()
        to_lines = json.dumps(to_state, indent=2).splitlines()
        
        diff = unified_diff(
            from_lines,
            to_lines,
            fromfile="previous",
            tofile="current",
            n=context_lines
        )
        
        return "\n".join(diff)
    
    async def get_visual_changes(
        self,
        entity_type: str,
        entity_id: str,
        from_version: int,
        to_version: int
    ) -> Dict[str, Any]:
        """Get visual representation of changes between versions."""
        changes = await self.get_changes_between_versions(
            entity_type,
            entity_id,
            from_version,
            to_version
        )
        
        # Generate unified diff
        unified_diff = self.generate_unified_diff(
            changes["from_version"]["current_state"],
            changes["to_version"]["current_state"]
        )
        
        return {
            "changes": changes,
            "unified_diff": unified_diff,
            "summary": self._generate_change_summary(changes["changes"])
        }
    
    def _generate_change_summary(self, changes: Dict[str, Any]) -> Dict[str, int]:
        """Generate a summary of changes."""
        summary = {
            "added": 0,
            "modified": 0,
            "removed": 0
        }
        
        for change in changes.values():
            summary[change["type"]] += 1
        
        return summary 