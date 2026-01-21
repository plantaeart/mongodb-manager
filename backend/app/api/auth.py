"""Authentication API endpoints"""

import os
from fastapi import APIRouter, HTTPException, Depends
from app.models.auth import (
    LoginRequest,
    LoginResponse,
    ChangePasswordRequest,
    FirstTimePasswordChangeRequest,
    AuthStatusResponse,
    MessageResponse
)
from app.core.auth import AuthManager
from app.middleware.auth import create_access_token, get_current_user

router = APIRouter()

# Initialize auth manager
auth_manager = AuthManager()


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    """Login with password and receive JWT token
    
    Returns JWT token on successful authentication.
    If using default password, requires password change before granting access.
    In development mode (NODE_ENV=development), skip password change requirement.
    """
    username = AuthManager.DEFAULT_USERNAME
    
    # Verify password
    if not auth_manager.verify_password(request.password, username):
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Check if we're in development mode
    node_env = os.getenv("NODE_ENV", "production").lower()
    is_development = node_env == "development"
    
    # Check if using default password (skip in development)
    if auth_manager.is_default_password(username) and not is_development:
        return LoginResponse(
            access_token="",
            username=username,
            needs_password_change=True,
            message="Default password must be changed before accessing the system"
        )
    
    # Create session in MongoDB
    auth_manager.create_session(username)
    
    # Generate JWT token
    token = create_access_token({"username": username})
    
    return LoginResponse(
        access_token=token,
        username=username,
        needs_password_change=False
    )


@router.post("/logout", response_model=MessageResponse)
def logout(user: dict = Depends(get_current_user)):
    """Logout and clear session"""
    username = user.get("username")
    
    # Clear session from MongoDB
    try:
        auth_manager.sessions_collection.delete_many({"username": username})
    except Exception:
        pass
    
    return MessageResponse(message="Logged out successfully")


@router.get("/status", response_model=AuthStatusResponse)
def status(user: dict = Depends(get_current_user)):
    """Check current authentication status"""
    username = user.get("username")
    
    # Get session info
    session = auth_manager.sessions_collection.find_one(
        {"username": username},
        sort=[("created_at", -1)]
    )
    
    return AuthStatusResponse(
        authenticated=True,
        username=username,
        session_expires=session.get("expires_at") if session else None
    )


@router.post("/change-password", response_model=MessageResponse)
def change_password(request: ChangePasswordRequest, user: dict = Depends(get_current_user)):
    """Change password for authenticated user"""
    username = user.get("username")
    
    # Verify old password
    if not auth_manager.verify_password(request.old_password, username):
        raise HTTPException(status_code=401, detail="Invalid old password")
    
    # Validate new password
    if len(request.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    
    # Update password
    new_hash = auth_manager.hash_password(request.new_password)
    success = auth_manager.update_user_password(username, new_hash)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update password")
    
    return MessageResponse(message="Password changed successfully")


@router.post("/first-time-password-change", response_model=LoginResponse)
def first_time_password_change(request: FirstTimePasswordChangeRequest):
    """Change password for first-time users with default password
    
    This endpoint doesn't require authentication since the user is logging in
    for the first time with the default password.
    """
    username = AuthManager.DEFAULT_USERNAME
    
    # Verify default password
    if not auth_manager.verify_password(request.old_password, username):
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Ensure they're using the default password
    if not auth_manager.is_default_password(username):
        raise HTTPException(status_code=400, detail="This endpoint is only for first-time password changes")
    
    # Validate new password
    if len(request.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    
    # Update password
    new_hash = auth_manager.hash_password(request.new_password)
    success = auth_manager.update_user_password(username, new_hash)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update password")
    
    # Create session
    auth_manager.create_session(username)
    
    # Generate JWT token
    token = create_access_token({"username": username})
    
    return LoginResponse(
        access_token=token,
        username=username,
        needs_password_change=False,
        message="Password changed successfully. You are now logged in."
    )
