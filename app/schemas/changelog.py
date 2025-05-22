from pydantic import BaseModel
from datetime import datetime
from typing import Any, Dict, List

# Schema for individual version history entries
class VersionHistoryEntry(BaseModel):
    version_number: int
    created_at: datetime
    user_id: int  # Assuming user_id is an integer
    # Include other relevant fields from the Version model if needed, e.g., a summary or identifier
    # state_summary: Optional[str] = None # Example

# Schema for the changelog response (list of version history entries)
class ChangelogResponse(BaseModel):
    event_id: int
    versions: List[VersionHistoryEntry]

# Schemas for the diff response

class ChangeSummary(BaseModel):
    added: int
    modified: int
    removed: int

class FieldChange(BaseModel):
    type: str # 'added', 'modified', 'removed'
    old_value: Any = None # Present for 'modified'
    new_value: Any = None # Present for 'added' and 'modified'
    value: Any = None # Present for 'removed'

class DetailedChanges(BaseModel):
    # Dictionary where keys are field names and values are FieldChange objects
    changes: Dict[str, FieldChange]

class DiffResponse(BaseModel):
    # Include details returned by get_visual_changes
    unified_diff: str
    summary: ChangeSummary
    # Potentially include detailed changes if needed on the frontend
    # detailed_changes: DetailedChanges 