"""Pydantic models for authentication"""

from pydantic import BaseModel, Field
from datetime import datetime


class LoginRequest(BaseModel):
    """Login request with password"""
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    """Login response with token"""
    access_token: str
    username: str
    needs_password_change: bool = False
    message: str | None = None


class ChangePasswordRequest(BaseModel):
    """Change password request"""
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


class AuthStatusResponse(BaseModel):
    """Authentication status response"""
    authenticated: bool
    username: str | None = None
    session_expires: datetime | None = None


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str


class FirstTimePasswordChangeRequest(BaseModel):
    """First-time password change request"""
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)
