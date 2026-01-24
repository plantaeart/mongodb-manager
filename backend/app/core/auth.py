"""Authentication and session management for MongoDB Manager"""

import os
import bcrypt
from pathlib import Path
from datetime import timedelta, datetime
import questionary
from rich.console import Console
from rich.panel import Panel

from .utils import (
    get_current_time,
    add_hours,
    is_expired,
    format_timestamp,
    ConfigManager,
    ensure_directory_exists,
)

console = Console()


class AuthManager:
    """Manages authentication and session handling using MongoDB"""
    
    DEFAULT_USERNAME = "admin"
    DEFAULT_PASSWORD = os.getenv("NUXT_ADMIN_PASSWORD", "admin123")
    SESSION_DURATION_HOURS = 24
    
    def __init__(self, session_dir: Path | None = None):
        """Initialize authentication manager with MongoDB backend
        
        Args:
            session_dir: Kept for backward compatibility but not used (sessions now in MongoDB)
        """
        # Initialize MongoDB connection
        self.db_client = ConfigManager.get_internal_db_client()
        self.users_collection = self.db_client.manager_app.users
        self.sessions_collection = self.db_client.manager_app.sessions
        
        # Create indexes for users collection
        self.users_collection.create_index("username", unique=True)
        
        # Create indexes for sessions collection
        self.sessions_collection.create_index("token", unique=True)
        self.sessions_collection.create_index("username")
        self.sessions_collection.create_index("expires_at", expireAfterSeconds=0)
        
        # Ensure default admin user exists
        self._ensure_default_user()
    
    def _ensure_default_user(self) -> None:
        """Ensure default admin user exists in database
        
        Creates admin user with default password if no users exist.
        """
        # Check if any users exist
        user_count = self.users_collection.count_documents({})
        
        if user_count == 0:
            # Create default admin user
            default_hash = self.hash_password(self.DEFAULT_PASSWORD)
            
            user_data = {
                'username': self.DEFAULT_USERNAME,
                'password_hash': default_hash,
                'is_default': True,
                'created_at': get_current_time(),
                'updated_at': get_current_time()
            }
            
            self.users_collection.insert_one(user_data)
            console.print(f"[yellow]Default admin user created (username: {self.DEFAULT_USERNAME}, password: {self.DEFAULT_PASSWORD})[/yellow]")
    
    def get_user(self, username: str) -> dict | None:
        """Get user from database
        
        Args:
            username: Username to retrieve
            
        Returns:
            User document or None if not found
        """
        return self.users_collection.find_one({"username": username})
    
    def update_user_password(self, username: str, new_password_hash: str) -> bool:
        """Update user password in database
        
        Args:
            username: Username to update
            new_password_hash: New bcrypt password hash
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.users_collection.update_one(
                {"username": username},
                {
                    "$set": {
                        "password_hash": new_password_hash,
                        "is_default": False,
                        "updated_at": get_current_time()
                    }
                }
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    def is_default_password(self, username: str) -> bool:
        """Check if user is using default password
        
        Args:
            username: Username to check
            
        Returns:
            True if using default password, False otherwise
        """
        user = self.get_user(username)
        if not user:
            return False
        return user.get('is_default', False)
    
    def check_session(self, username: str = None) -> bool:
        """Check if current session is valid (MongoDB-backed)
        
        Args:
            username: Optional username to check session for (defaults to admin)
            
        Returns:
            True if session exists and not expired, False otherwise
        """
        if username is None:
            username = self.DEFAULT_USERNAME
            
        try:
            # Find any session for this user that hasn't expired yet
            session = self.sessions_collection.find_one(
                {
                    "username": username,
                    "expires_at": {"$gt": get_current_time()}
                },
                sort=[("created_at", -1)]
            )
            return session is not None
        except Exception:
            return False
    
    def create_session(self, username: str = None) -> None:
        """Create a new session with 24h expiration (stored in MongoDB)
        
        Args:
            username: Username to create session for (defaults to admin)
        """
        import uuid
        
        if username is None:
            username = self.DEFAULT_USERNAME
        
        now = get_current_time()
        expires = add_hours(now, self.SESSION_DURATION_HOURS)
        
        session_data = {
            'username': username,
            'token': str(uuid.uuid4()),
            'created_at': now,
            'expires_at': expires,
            'last_accessed': now
        }
        
        # Clear old sessions for this user
        self.sessions_collection.delete_many({"username": username})
        # Insert new session
        self.sessions_collection.insert_one(session_data)
    
    def verify_password(self, password: str, username: str = None) -> bool:
        """Verify password against stored hash in MongoDB
        
        Args:
            password: Password to verify
            username: Username to verify (defaults to admin)
            
        Returns:
            True if password matches hash, False otherwise
        """
        if username is None:
            username = self.DEFAULT_USERNAME
            
        user = self.get_user(username)
        if not user:
            return False
        
        password_hash = user.get('password_hash')
        if not password_hash:
            return False
        
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
        except Exception:
            return False
    
    def hash_password(self, password: str) -> str:
        """Generate bcrypt hash for password
        
        Args:
            password: Password to hash
            
        Returns:
            Bcrypt hash as string
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def _prompt_new_password(self, username: str = None) -> bool:
        """Prompt user for new password with confirmation and save to MongoDB
        
        Args:
            username: Username to update (defaults to admin)
            
        Returns:
            True if successful, False if failed
        """
        if username is None:
            username = self.DEFAULT_USERNAME
            
        new_password = questionary.password("Enter new password:").ask()
        if not new_password:
            return False
        
        # Password validation
        if len(new_password) < 8:
            console.print("[red]ERROR[/red] Password must be at least 8 characters!")
            return False
        
        confirm_password = questionary.password("Confirm new password:").ask()
        
        if new_password != confirm_password:
            console.print("[red]ERROR[/red] Passwords don't match!")
            return False
        
        # Hash password and update in MongoDB
        new_hash = self.hash_password(new_password)
        success = self.update_user_password(username, new_hash)
        
        if success:
            console.print("[green]✓ Password changed successfully![/green]")
            console.print("[cyan]Your new password is now active. No restart needed![/cyan]")
            return True
        else:
            console.print("[red]ERROR[/red] Failed to update password in database")
            return False
    
    
    def prompt_login(self, username: str = None) -> bool:
        """Prompt for password and handle authentication flow
        
        Automatically prompts for password change if using default password.
        
        Args:
            username: Username to login as (defaults to admin)
        
        Returns:
            True if authentication successful, False otherwise
        """
        if username is None:
            username = self.DEFAULT_USERNAME
            
        password = questionary.password("Enter password:").ask()
        
        if not password:
            return False
        
        # Check if password is correct
        if not self.verify_password(password, username):
            console.print("[red]ERROR[/red] Incorrect password")
            return False
        
        # Check if using default password - force change
        if self.is_default_password(username):
            console.print("\n[yellow]⚠️  You are using the default password![/yellow]")
            console.print("[yellow]For security, you must change it now.[/yellow]\n")
            
            # Force password change immediately
            if self._prompt_new_password(username):
                # Create session (user can continue working)
                self.create_session(username)
                return True
            else:
                console.print("[red]ERROR[/red] Password change failed. Please try again.")
                return False
        
        # Normal flow - create session
        self.create_session(username)
        return True
    
    
    def prompt_password_change(self, username: str = None) -> bool:
        """Prompt user to change their password (for auth change command)
        
        Args:
            username: Username to change password for (defaults to admin)
        
        Returns:
            True if successful, False otherwise
        """
        if username is None:
            username = self.DEFAULT_USERNAME
            
        # Verify current password first
        current_password = questionary.password("Enter current password:").ask()
        
        if not current_password:
            return False
        
        if not self.verify_password(current_password, username):
            console.print("[red]ERROR[/red] Current password is incorrect")
            return False
        
        # Get new password and update
        return self._prompt_new_password(username)
    
    
    def logout(self, username: str = None) -> None:
        """Logout by deleting sessions from MongoDB
        
        Args:
            username: Username to logout (defaults to admin, None means all)
        """
        if username is None:
            username = self.DEFAULT_USERNAME
        self.sessions_collection.delete_many({"username": username})
    
    def get_session_info(self, username: str = None) -> dict | None:
        """Get current session information from MongoDB
        
        Args:
            username: Username to get session for (defaults to admin)
        
        Returns:
            Session info dict or None if no valid session
        """
        if username is None:
            username = self.DEFAULT_USERNAME
            
        try:
            # Find active session for this user
            session = self.sessions_collection.find_one(
                {
                    "username": username,
                    "expires_at": {"$gt": get_current_time()}
                },
                sort=[("created_at", -1)]
            )
            
            if not session:
                return None
            
            expires_at = session['expires_at']
            
            # Calculate time remaining
            now = get_current_time()
            time_remaining = expires_at - now
            
            # Update last accessed timestamp
            self.sessions_collection.update_one(
                {"_id": session["_id"]},
                {"$set": {"last_accessed": now}}
            )
            
            return {
                'username': username,
                'expires_at': expires_at,
                'time_remaining': time_remaining,
                'is_valid': time_remaining.total_seconds() > 0
            }
        except Exception:
            return None
