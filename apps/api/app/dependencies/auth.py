"""
Authentication dependencies for FastAPI.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fbx_core.auth.auth_handler import auth_handler, TokenData, UserRole


# Security scheme for JWT Bearer token
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """
    Get the current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer credentials containing the JWT token
        
    Returns:
        TokenData with user information
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    token_data = auth_handler.validate_token(token)
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_data


async def get_current_active_user(
    current_user: TokenData = Depends(get_current_user)
) -> TokenData:
    """
    Ensure the current user is active.
    
    Args:
        current_user: Current user token data
        
    Returns:
        TokenData if user is active
        
    Raises:
        HTTPException: If user is inactive
    """
    # In a real app, you would check the database here
    # For now, we'll assume all authenticated users are active
    return current_user


def require_role(required_role: UserRole):
    """
    Dependency factory to require a specific role or higher.
    
    Args:
        required_role: Minimum required role level
        
    Returns:
        Dependency function that validates user role
    """
    async def role_checker(
        current_user: TokenData = Depends(get_current_active_user)
    ) -> TokenData:
        if not auth_handler.check_permission(current_user.role, required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role.value}"
            )
        return current_user
    
    return role_checker


# Convenience dependencies for common role requirements
require_user = require_role(UserRole.USER)
require_moderator = require_role(UserRole.MODERATOR)
require_admin = require_role(UserRole.ADMIN)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[TokenData]:
    """
    Get the current user if authenticated, otherwise return None.
    
    This is useful for endpoints that have different behavior
    for authenticated vs unauthenticated users.
    
    Args:
        credentials: Optional HTTP Bearer credentials
        
    Returns:
        TokenData if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    return auth_handler.validate_token(token)