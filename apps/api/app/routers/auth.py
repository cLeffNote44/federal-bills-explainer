"""
User authentication and registration API endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import uuid

from fbx_core.auth.utils import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    validate_email,
    validate_username,
    validate_password,
    get_gravatar_url,
    generate_verification_token,
    generate_reset_token,
)

router = APIRouter()


# Pydantic models
class UserRegistration(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserProfile(BaseModel):
    id: str
    email: str
    username: str
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    reputation: int = 0
    is_verified: bool = False
    created_at: datetime


class PasswordReset(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


# In-memory user storage (replace with database in production)
users_db = {}
user_emails = {}


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegistration):
    """
    Register a new user account.

    Creates a new user with email verification.
    """
    # Validate email
    if not validate_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )

    # Validate username
    if not validate_username(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be 3-50 alphanumeric characters or underscores"
        )

    # Validate password
    is_valid, error_msg = validate_password(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    # Check if email already exists
    if user_data.email in user_emails:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Check if username already exists
    if any(u["username"] == user_data.username for u in users_db.values()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    # Create user
    user_id = str(uuid.uuid4())
    hashed_pwd = hash_password(user_data.password)
    verification_token = generate_verification_token()

    user = {
        "id": user_id,
        "email": user_data.email,
        "username": user_data.username,
        "hashed_password": hashed_pwd,
        "full_name": user_data.full_name,
        "avatar_url": get_gravatar_url(user_data.email),
        "is_active": True,
        "is_verified": False,
        "is_admin": False,
        "reputation": 0,
        "created_at": datetime.utcnow(),
        "verification_token": verification_token,
    }

    users_db[user_id] = user
    user_emails[user_data.email] = user_id

    # TODO: Send verification email
    # send_verification_email(user_data.email, verification_token)

    # Create tokens
    access_token = create_access_token({"sub": user_id, "email": user_data.email})
    refresh_token = create_refresh_token({"sub": user_id})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """
    Login with email and password.

    Returns access and refresh tokens.
    """
    # Find user by email
    user_id = user_emails.get(credentials.email)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    user = users_db[user_id]

    # Verify password
    if not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Check if user is active
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )

    # Update last login
    user["last_login"] = datetime.utcnow()

    # Create tokens
    access_token = create_access_token({"sub": user_id, "email": credentials.email})
    refresh_token = create_refresh_token({"sub": user_id})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str):
    """
    Refresh access token using refresh token.
    """
    payload = decode_token(refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    user_id = payload.get("sub")
    if not user_id or user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    user = users_db[user_id]

    # Create new tokens
    access_token = create_access_token({"sub": user_id, "email": user["email"]})
    new_refresh_token = create_refresh_token({"sub": user_id})

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserProfile)
async def get_current_user(token: str = Depends(lambda: None)):
    """
    Get current user profile.

    Requires authentication token.
    """
    # TODO: Extract token from Authorization header
    # For now, return mock data
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required"
    )


@router.post("/password-reset")
async def request_password_reset(data: PasswordReset):
    """
    Request password reset email.

    Sends reset link to user's email.
    """
    user_id = user_emails.get(data.email)

    # Don't reveal if email exists (security)
    if not user_id:
        return {"message": "If the email exists, a reset link has been sent"}

    user = users_db[user_id]

    # Generate reset token
    reset_token = generate_reset_token()
    user["reset_token"] = reset_token
    user["reset_sent_at"] = datetime.utcnow()

    # TODO: Send reset email
    # send_password_reset_email(data.email, reset_token)

    return {"message": "If the email exists, a reset link has been sent"}


@router.post("/password-reset/confirm")
async def confirm_password_reset(data: PasswordResetConfirm):
    """
    Confirm password reset with token.

    Sets new password for user.
    """
    # Find user with reset token
    user = None
    for u in users_db.values():
        if u.get("reset_token") == data.token:
            user = u
            break

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    # Check token expiry (24 hours)
    reset_sent = user.get("reset_sent_at")
    if reset_sent:
        elapsed = datetime.utcnow() - reset_sent
        if elapsed.total_seconds() > 86400:  # 24 hours
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has expired"
            )

    # Validate new password
    is_valid, error_msg = validate_password(data.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    # Update password
    user["hashed_password"] = hash_password(data.new_password)
    user["reset_token"] = None
    user["reset_sent_at"] = None

    return {"message": "Password reset successful"}


@router.post("/verify-email/{token}")
async def verify_email(token: str):
    """
    Verify email address with token.
    """
    # Find user with verification token
    user = None
    for u in users_db.values():
        if u.get("verification_token") == token:
            user = u
            break

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )

    # Mark as verified
    user["is_verified"] = True
    user["verified_at"] = datetime.utcnow()
    user["verification_token"] = None

    return {"message": "Email verified successfully"}
