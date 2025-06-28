# backend/services/api-server/src/models/auth.py

import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel, EmailStr, Field

from src.shared.db.database import Base 

# =================================================================
# Placeholder Constants (to make schemas self-contained)
# ในโปรเจคจริง ควรกำหนดค่าเหล่านี้ในไฟล์ constants.py
# =================================================================
class Validation:
    MIN_PASSWORD_LENGTH = 8

class OAuth:
    GOOGLE = "google"
# =================================================================


# =================================================================
# SQLAlchemy ORM Model (สำหรับ Database)
# =================================================================
class User(Base):
    """
    Represents the User model in our public.users table.
    This table stores public information related to a user from Supabase Auth.
    """
    __tablename__ = "users"

    # This ID should correspond to the ID from Supabase's auth.users table.
    id = Column(UUID(as_uuid=True), primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# =================================================================
# Pydantic Schemas (สำหรับ API Request/Response)
# =================================================================

class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr


class UserCreate(UserBase):
    """User creation schema"""
    password: str = Field(..., min_length=Validation.MIN_PASSWORD_LENGTH)
    full_name: str = Field(..., min_length=1)


class UserLogin(UserBase):
    """User login schema"""
    password: str


class UserResponse(UserBase):
    """User response schema"""
    id: uuid.UUID
    full_name: str
    created_at: datetime | None = None

    class Config:
        # orm_mode = True
        from_attributes = True # Pydantic V2

class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str = ""
    refresh_token: str = ""
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    """Authentication response schema"""
    user: UserResponse
    token: TokenResponse


class PasswordResetRequest(BaseModel):
    """Password reset request schema"""
    email: EmailStr


class OAuthProvider(str, Enum):
    """OAuth provider options"""
    GOOGLE = OAuth.GOOGLE


class OAuthLoginRequest(BaseModel):
    """OAuth login initiation request"""
    provider: OAuthProvider
    redirect_url: str


class OAuthCallbackRequest(BaseModel):
    """OAuth callback request"""
    provider: OAuthProvider
    code: str
    redirect_url: str


class OAuthResponse(BaseModel):
    """OAuth login response"""
    auth_url: str