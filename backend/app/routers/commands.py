"""HTTP API endpoints for command execution"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any
import io
import sys
from contextlib import redirect_stdout, redirect_stderr

from app.core.cli import app as cli_app
from app.middleware.auth import get_current_user
from app.core.utils.uri_builder import build_mongodb_uri

router = APIRouter(prefix="/api/commands", tags=["commands"])


class CommandExecuteRequest(BaseModel):
    """Request model for command execution"""
    command: str  # e.g., "connect add"
    params: Dict[str, Any]  # e.g., {"name": "my-db", "uri": "mongodb://..."}


class CommandExecuteResponse(BaseModel):
    """Response model for command execution"""
    success: bool
    output: str
    error: str | None = None
    exit_code: int = 0


@router.post("/execute", response_model=CommandExecuteResponse)
async def execute_command(
    request: CommandExecuteRequest,
    current_user: dict = Depends(get_current_user)
):
    """Execute a CLI command with parameters via HTTP
    
    This endpoint allows executing CLI commands without WebSocket,
    which is useful for form-based commands that don't need streaming output.
    
    Supports two modes for 'connect add' command:
    - Simple mode: params contain 'uri' field with complete MongoDB URI
    - Advanced mode: params contain 'host', 'port', 'username', 'password' fields
                     and URI is automatically constructed
    
    Args:
        request: Command and parameters to execute
        
    Returns:
        Command execution result with output
        
    Examples:
        Simple mode:
        {
            "command": "connect add",
            "params": {
                "name": "my-db",
                "uri": "mongodb://localhost:27017",
                "description": "Test database"
            }
        }
        
        Advanced mode:
        {
            "command": "connect add",
            "params": {
                "name": "my-db",
                "host": "localhost",
                "port": 27017,
                "username": "admin",
                "password": "secret",
                "auth_source": "admin",
                "database": "mydb",
                "description": "Test database",
                "_mode": "advanced"
            }
        }
        
        Response:
        {
            "success": true,
            "output": "✓ Connection 'my-db' added successfully",
            "error": null,
            "exit_code": 0
        }
    """
    # Check if this is advanced mode (has host/port instead of uri)
    if "_mode" in request.params and request.params["_mode"] == "advanced":
        # Advanced mode: build URI from components
        try:
            uri = build_mongodb_uri(
                host=request.params.get("host", "localhost"),
                port=int(request.params.get("port", 27017)),
                username=request.params.get("username") or None,
                password=request.params.get("password") or None,
                database=request.params.get("database") or None,
                auth_source=request.params.get("auth_source", "admin")
            )
            
            # Replace params with constructed URI for CLI
            request.params = {
                "name": request.params["name"],
                "uri": uri,
                "description": request.params.get("description", "")
            }
        except ValueError as e:
            return CommandExecuteResponse(
                success=False,
                output="",
                error=f"Invalid connection parameters: {str(e)}",
                exit_code=1
            )
    
    # Build CLI arguments from command and params
    cmd_parts = request.command.strip().split()
    
    # Add parameters as CLI options (skip internal parameters like _mode)
    for key, value in request.params.items():
        if key.startswith("_"):
            # Skip internal parameters (like _mode)
            continue
        if value is not None and value != "":
            cmd_parts.append(f"--{key}")
            cmd_parts.append(str(value))
    
    # Capture stdout and stderr
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    exit_code = 0
    
    try:
        # Redirect output streams
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            try:
                # Execute CLI command (synchronous - no event loop issues!)
                cli_app(cmd_parts, standalone_mode=False)
            except SystemExit as e:
                exit_code = e.code if e.code is not None else 0
            except Exception as e:
                exit_code = 1
                stderr_capture.write(f"Error: {str(e)}\n")
        
        # Get captured output
        output = stdout_capture.getvalue()
        error = stderr_capture.getvalue()
        
        return CommandExecuteResponse(
            success=(exit_code == 0),
            output=output,
            error=error if error else None,
            exit_code=exit_code
        )
        
    except Exception as e:
        # Unexpected error in request handling
        return CommandExecuteResponse(
            success=False,
            output="",
            error=f"Failed to execute command: {str(e)}",
            exit_code=1
        )
    finally:
        stdout_capture.close()
        stderr_capture.close()
