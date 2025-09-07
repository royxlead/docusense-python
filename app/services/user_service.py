"""
User authentication and management service.

This module provides functions for user authentication, authorization,
and role-based access control.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import hashlib
import secrets
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token security
security = HTTPBearer(auto_error=False)

# Mock user database (in production, use a real database)
MOCK_USERS = {
    "admin": {
        "user_id": "admin",
        "username": "admin",
        "email": "admin@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
        "role": "admin",
        "is_active": True,
        "created_at": "2025-01-01T00:00:00",
        "last_login": None
    },
    "user": {
        "user_id": "user1",
        "username": "user",
        "email": "user@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
        "role": "user",
        "is_active": True,
        "created_at": "2025-01-01T00:00:00",
        "last_login": None
    }
}


def authenticate_user(username: str, password: str) -> bool:
    """
    Authenticate a user with username and password.
    
    This function verifies user credentials against the user database
    and returns True if authentication is successful.
    
    Args:
        username: Username for authentication
        password: Plain text password
        
    Returns:
        bool: True if authentication successful, False otherwise
    """
    try:
        if not username or not password:
            logger.warning("Authentication attempted with empty credentials")
            return False
        
        logger.info(f"Authentication attempt for user: {username}")
        
        # Get user from database
        user = get_user_by_username(username)
        if not user:
            logger.warning(f"User not found: {username}")
            return False
        
        # Check if user is active
        if not user.get("is_active", False):
            logger.warning(f"Inactive user attempted login: {username}")
            return False
        
        # Verify password
        hashed_password = user.get("hashed_password", "")
        if not verify_password(password, hashed_password):
            logger.warning(f"Invalid password for user: {username}")
            return False
        
        # Update last login
        _update_last_login(username)
        
        logger.info(f"Successful authentication for user: {username}")
        return True
        
    except Exception as e:
        logger.error(f"Authentication error for user {username}: {str(e)}")
        return False


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database
        
    Returns:
        bool: True if password matches
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def get_password_hash(password: str) -> str:
    """
    Generate password hash.
    
    Args:
        password: Plain text password
        
    Returns:
        str: Hashed password
    """
    try:
        return pwd_context.hash(password)
    except Exception as e:
        logger.error(f"Password hashing error: {e}")
        return ""


def get_user_role(username: str) -> str:
    """
    Get the role of a user.
    
    This function retrieves the role assigned to a user for
    role-based access control decisions.
    
    Args:
        username: Username to get role for
        
    Returns:
        str: User role (admin, user, etc.) or 'guest' if not found
    """
    try:
        user = get_user_by_username(username)
        if user:
            role = user.get("role", "guest")
            logger.debug(f"User {username} has role: {role}")
            return role
        else:
            logger.warning(f"Role requested for unknown user: {username}")
            return "guest"
            
    except Exception as e:
        logger.error(f"Error getting role for user {username}: {str(e)}")
        return "guest"


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve user data by username.
    
    Args:
        username: Username to look up
        
    Returns:
        Optional[Dict[str, Any]]: User data or None if not found
    """
    try:
        return MOCK_USERS.get(username)
    except Exception as e:
        logger.error(f"Error retrieving user {username}: {e}")
        return None


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve user data by user ID.
    
    Args:
        user_id: User ID to look up
        
    Returns:
        Optional[Dict[str, Any]]: User data or None if not found
    """
    try:
        for user in MOCK_USERS.values():
            if user.get("user_id") == user_id:
                return user
        return None
    except Exception as e:
        logger.error(f"Error retrieving user by ID {user_id}: {e}")
        return None


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time
        
    Returns:
        str: Encoded JWT token
    """
    try:
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        
        logger.debug(f"Created access token for: {data.get('sub', 'unknown')}")
        return encoded_jwt
        
    except Exception as e:
        logger.error(f"Token creation error: {e}")
        return ""


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token to verify
        
    Returns:
        Optional[Dict[str, Any]]: Decoded token data or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        username = payload.get("sub")
        if username is None:
            return None
        
        return payload
        
    except JWTError as e:
        logger.warning(f"Invalid token: {e}")
        return None
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return None


def get_current_user_from_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Get current user from JWT token.
    
    Args:
        token: JWT token
        
    Returns:
        Optional[Dict[str, Any]]: User data or None if invalid
    """
    try:
        payload = verify_token(token)
        if not payload:
            return None
        
        username = payload.get("sub")
        if not username:
            return None
        
        user = get_user_by_username(username)
        if not user:
            return None
        
        if not user.get("is_active", False):
            return None
        
        return user
        
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        return None


def check_permission(user_role: str, required_role: str) -> bool:
    """
    Check if user role has sufficient permissions.
    
    Args:
        user_role: Current user's role
        required_role: Required role for the operation
        
    Returns:
        bool: True if user has sufficient permissions
    """
    try:
        # Define role hierarchy
        role_hierarchy = {
            "guest": 0,
            "user": 1,
            "admin": 2,
            "superadmin": 3
        }
        
        user_level = role_hierarchy.get(user_role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        has_permission = user_level >= required_level
        
        logger.debug(f"Permission check: {user_role}({user_level}) >= {required_role}({required_level}) = {has_permission}")
        
        return has_permission
        
    except Exception as e:
        logger.error(f"Permission check error: {e}")
        return False


def create_user(
    username: str,
    email: str,
    password: str,
    role: str = "user"
) -> Dict[str, Any]:
    """
    Create a new user account.
    
    Args:
        username: Username for the new account
        email: Email address
        password: Plain text password
        role: User role
        
    Returns:
        Dict[str, Any]: Result of user creation
    """
    try:
        # Check if user already exists
        if get_user_by_username(username):
            return {
                "success": False,
                "error": "Username already exists"
            }
        
        # Validate input
        if not username or not email or not password:
            return {
                "success": False,
                "error": "Missing required fields"
            }
        
        if len(password) < 6:
            return {
                "success": False,
                "error": "Password must be at least 6 characters"
            }
        
        # Create user
        user_id = f"user_{secrets.token_hex(8)}"
        hashed_password = get_password_hash(password)
        
        new_user = {
            "user_id": user_id,
            "username": username,
            "email": email,
            "hashed_password": hashed_password,
            "role": role,
            "is_active": True,
            "created_at": datetime.utcnow().isoformat(),
            "last_login": None
        }
        
        # Add to mock database
        MOCK_USERS[username] = new_user
        
        logger.info(f"Created new user: {username} with role: {role}")
        
        return {
            "success": True,
            "user_id": user_id,
            "message": "User created successfully"
        }
        
    except Exception as e:
        logger.error(f"User creation error: {e}")
        return {
            "success": False,
            "error": f"User creation failed: {str(e)}"
        }


def update_user_role(username: str, new_role: str, admin_user: str) -> Dict[str, Any]:
    """
    Update a user's role.
    
    Args:
        username: Username to update
        new_role: New role to assign
        admin_user: Username of admin performing the update
        
    Returns:
        Dict[str, Any]: Result of role update
    """
    try:
        # Check admin permissions
        admin_role = get_user_role(admin_user)
        if not check_permission(admin_role, "admin"):
            return {
                "success": False,
                "error": "Insufficient permissions"
            }
        
        # Get user to update
        user = get_user_by_username(username)
        if not user:
            return {
                "success": False,
                "error": "User not found"
            }
        
        # Update role
        old_role = user.get("role", "guest")
        MOCK_USERS[username]["role"] = new_role
        
        logger.info(f"Updated user {username} role from {old_role} to {new_role} by {admin_user}")
        
        return {
            "success": True,
            "message": f"Role updated from {old_role} to {new_role}"
        }
        
    except Exception as e:
        logger.error(f"Role update error: {e}")
        return {
            "success": False,
            "error": f"Role update failed: {str(e)}"
        }


def _update_last_login(username: str) -> None:
    """
    Update the last login timestamp for a user.
    
    Args:
        username: Username to update
    """
    try:
        if username in MOCK_USERS:
            MOCK_USERS[username]["last_login"] = datetime.utcnow().isoformat()
    except Exception as e:
        logger.warning(f"Failed to update last login for {username}: {e}")


def get_user_statistics() -> Dict[str, Any]:
    """
    Get statistics about users.
    
    Returns:
        Dict[str, Any]: User statistics
    """
    try:
        stats = {
            "total_users": len(MOCK_USERS),
            "active_users": 0,
            "inactive_users": 0,
            "roles": {},
            "recent_logins": 0
        }
        
        # Analyze users
        recent_threshold = datetime.utcnow() - timedelta(days=7)
        
        for user in MOCK_USERS.values():
            # Active/inactive count
            if user.get("is_active", False):
                stats["active_users"] += 1
            else:
                stats["inactive_users"] += 1
            
            # Role distribution
            role = user.get("role", "unknown")
            stats["roles"][role] = stats["roles"].get(role, 0) + 1
            
            # Recent logins
            last_login_str = user.get("last_login")
            if last_login_str:
                try:
                    last_login = datetime.fromisoformat(last_login_str.replace('Z', '+00:00'))
                    if last_login > recent_threshold:
                        stats["recent_logins"] += 1
                except ValueError:
                    pass
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get user statistics: {e}")
        return {"error": str(e)}


async def get_current_user_dependency(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """
    FastAPI dependency to get current user from Authorization header.
    
    Args:
        credentials: HTTP Authorization credentials
        
    Returns:
        Optional[Dict[str, Any]]: User data or None if no valid token
    """
    try:
        if not credentials:
            return None
        
        token = credentials.credentials
        return get_current_user_from_token(token)
        
    except Exception as e:
        logger.error(f"Error in get_current_user_dependency: {e}")
        return None


# Alias for backward compatibility
get_current_user = get_current_user_dependency