"""JWT authentication middleware"""

from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from datetime import datetime, timedelta
import os

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET", "change-me-in-production-please-use-strong-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

security = HTTPBearer()


def create_access_token(data: dict) -> str:
    """Create JWT access token
    
    Args:
        data: Payload data to encode (e.g., {"username": "admin"})
        
    Returns:
        JWT token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """Verify JWT token and return payload
    
    Args:
        token: JWT token string
        
    Returns:
        Token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("username")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")


def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """Dependency to get current authenticated user
    
    Args:
        credentials: HTTP Bearer token from request
        
    Returns:
        User payload from token
        
    Raises:
        HTTPException: If token is invalid
    """
    token = credentials.credentials
    return verify_token(token)
