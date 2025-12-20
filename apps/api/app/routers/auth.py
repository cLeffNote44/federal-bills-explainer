"""Authentication router for user management."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt

from fbx_core.db.session import SessionLocal
from fbx_core.models.tables import User
from fbx_core.utils.settings import Settings

router = APIRouter()
settings = Settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = settings.jwt_secret_key or "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 1 week


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    display_name: Optional[str]
    is_verified: bool
    email_notifications: bool
    notification_frequency: str
    zip_code: Optional[str]
    state: Optional[str]


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    email_notifications: Optional[bool] = None
    notification_frequency: Optional[str] = None
    zip_code: Optional[str] = None
    state: Optional[str] = None
    preferences: Optional[dict] = None


@router.post("/register", response_model=AuthResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if user exists
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    user = User(
        email=request.email,
        password_hash=get_password_hash(request.password),
        display_name=request.display_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create token
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return AuthResponse(
        access_token=access_token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            is_verified=user.is_verified,
            email_notifications=user.email_notifications,
            notification_frequency=user.notification_frequency,
            zip_code=user.zip_code,
            state=user.state,
        )
    )


@router.post("/login", response_model=AuthResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Log in an existing user."""
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Update last login
    user.last_login_at = datetime.utcnow()
    db.commit()

    # Create token
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return AuthResponse(
        access_token=access_token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            is_verified=user.is_verified,
            email_notifications=user.email_notifications,
            notification_frequency=user.notification_frequency,
            zip_code=user.zip_code,
            state=user.state,
        )
    )


def get_current_user(token: str, db: Session) -> User:
    """Extract user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


@router.get("/me", response_model=UserResponse)
def get_me(authorization: str = None, db: Session = Depends(get_db)):
    """Get current user profile."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.split(" ")[1]
    user = get_current_user(token, db)

    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        is_verified=user.is_verified,
        email_notifications=user.email_notifications,
        notification_frequency=user.notification_frequency,
        zip_code=user.zip_code,
        state=user.state,
    )


@router.patch("/profile", response_model=UserResponse)
def update_profile(
    request: ProfileUpdateRequest,
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Update user profile."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.split(" ")[1]
    user = get_current_user(token, db)

    # Update fields
    if request.display_name is not None:
        user.display_name = request.display_name
    if request.email_notifications is not None:
        user.email_notifications = request.email_notifications
    if request.notification_frequency is not None:
        user.notification_frequency = request.notification_frequency
    if request.zip_code is not None:
        user.zip_code = request.zip_code
    if request.state is not None:
        user.state = request.state
    if request.preferences is not None:
        user.preferences = request.preferences

    db.commit()
    db.refresh(user)

    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        is_verified=user.is_verified,
        email_notifications=user.email_notifications,
        notification_frequency=user.notification_frequency,
        zip_code=user.zip_code,
        state=user.state,
    )


@router.post("/logout")
def logout():
    """Log out (client should discard token)."""
    return {"message": "Logged out successfully"}
