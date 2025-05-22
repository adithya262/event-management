
from typing import List
from functools import wraps
from fastapi import HTTPException, status
from app.models.user import UserRole

def check_permissions(required_roles: List[UserRole]):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated"
                )
            
            if current_user.role not in required_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Role-based dependencies
owner_required = check_permissions([UserRole.OWNER])
editor_required = check_permissions([UserRole.OWNER, UserRole.EDITOR])
viewer_required = check_permissions([UserRole.OWNER, UserRole.EDITOR, UserRole.VIEWER]) 