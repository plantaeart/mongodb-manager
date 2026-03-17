"""HTTP API endpoints for command execution"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any
import io
import sys
import json
import logging
from contextlib import redirect_stdout, redirect_stderr

from app.core.cli import app as cli_app
from app.middleware.auth import get_current_user
from app.core.utils.uri_builder import build_mongodb_uri

logger = logging.getLogger(__name__)
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
    
    Connection commands use component-based parameters:
    - params contain 'host', 'port', 'username', 'password', 'database', 'auth_source' fields
    - URIs are automatically constructed by the backend when connecting to MongoDB
    
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
    # For connect add/update commands, ensure port is an integer
    if request.command.strip() in ["connect add", "connect update"]:
        if "port" in request.params:
            port_value = request.params["port"]
            
            # Convert empty string to default port
            if isinstance(port_value, str):
                if port_value.strip() == '':
                    request.params["port"] = 27017
                else:
                    request.params["port"] = int(port_value)
            elif port_value is None:
                request.params["port"] = 27017
        else:
            # No port provided, set default
            request.params["port"] = 27017
    
    # Special handling for 'connect remove' with multiple connections
    if request.command.strip() == "connect remove" and "connections" in request.params:
        # connections is an array of connection names to remove
        connections_to_remove = request.params.get("connections", [])
        
        if not isinstance(connections_to_remove, list):
            connections_to_remove = [connections_to_remove]
        
        if not connections_to_remove:
            return CommandExecuteResponse(
                success=False,
                output="",
                error="No connections selected",
                exit_code=1
            )
        
        # Remove connections one by one and collect results
        success_count = 0
        failed_count = 0
        all_output = []
        all_errors = []
        
        for conn_name in connections_to_remove:
            single_cmd_parts = ["connect", "remove", "--name", conn_name, "--yes"]
            
            # Capture output for this single removal
            single_stdout = io.StringIO()
            single_stderr = io.StringIO()
            single_exit_code = 0
            
            try:
                with redirect_stdout(single_stdout), redirect_stderr(single_stderr):
                    try:
                        cli_app(single_cmd_parts, standalone_mode=False)
                    except SystemExit as e:
                        single_exit_code = e.code if e.code is not None else 0
                    except Exception as e:
                        single_exit_code = 1
                        single_stderr.write(f"Error: {str(e)}\n")
                
                stdout_val = single_stdout.getvalue()
                stderr_val = single_stderr.getvalue()
                
                if single_exit_code != 0:
                    failed_count += 1
                    all_errors.append(stderr_val)
                else:
                    all_output.append(stdout_val)
            
            finally:
                single_stdout.close()
                single_stderr.close()
        
        # Build combined response
        success_count = len(connections_to_remove) - failed_count
        combined_output = "\n".join(all_output)
        combined_errors = "\n".join(all_errors)
        
        # Add summary
        if success_count > 0:
            combined_output += f"\n✓ Successfully removed {success_count} connection(s)"
        if failed_count > 0:
            combined_errors += f"\n✗ Failed to remove {failed_count} connection(s)"
        
        return CommandExecuteResponse(
            success=(failed_count == 0),
            output=combined_output,
            error=combined_errors if combined_errors else None,
            exit_code=0 if failed_count == 0 else 1
        )
    
    # Special handling for 'connect test' with multiple connections
    if request.command.strip() == "connect test" and "connections" in request.params:
        # connections is an array of connection names to test
        connections_to_test = request.params.get("connections", [])
        
        if not isinstance(connections_to_test, list):
            connections_to_test = [connections_to_test]
        
        if not connections_to_test:
            return CommandExecuteResponse(
                success=False,
                output="",
                error="No connections selected",
                exit_code=1
            )
        
        # Build command with comma-separated names and JSON output flag
        names_param = ",".join(connections_to_test)
        cmd_parts = ["connect", "test", "--names", names_param, "--yes", "--json"]
        
        # Capture output
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        exit_code = 0
        
        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                try:
                    cli_app(cmd_parts, standalone_mode=False)
                except SystemExit as e:
                    exit_code = e.code if e.code is not None else 0
                except Exception as e:
                    exit_code = 1
                    stderr_capture.write(f"Error: {str(e)}\n")
            
            output = stdout_capture.getvalue()
            error = stderr_capture.getvalue()
            
            # Parse JSON output and format for display
            try:
                result_data = json.loads(output)
                results = result_data.get("results", [])
                summary = result_data.get("summary", {})
                
                # Format output with colors/icons for terminal display
                formatted_lines = []
                formatted_lines.append(f"Testing {summary.get('total', 0)} connection(s):")
                formatted_lines.append("")  # Empty line for spacing
                
                for result in results:
                    name = result.get("name", "unknown")
                    success = result.get("success", False)
                    message = result.get("message", "")
                    
                    if success:
                        formatted_lines.append(f"✓ {name}")
                        formatted_lines.append(f"  Status: Connected successfully")
                        formatted_lines.append(f"  Details: {message}")
                    else:
                        formatted_lines.append(f"✗ {name}")
                        formatted_lines.append(f"  Status: Connection failed")
                        formatted_lines.append(f"  Error: {message}")
                    formatted_lines.append("")  # Empty line between results
                
                formatted_lines.append(f"Summary: {summary.get('success', 0)} successful, {summary.get('failure', 0)} failed")
                
                formatted_output = "\n".join(formatted_lines)
                
                return CommandExecuteResponse(
                    success=(exit_code == 0),
                    output=formatted_output,
                    error=error if error else None,
                    exit_code=exit_code
                )
            except json.JSONDecodeError as e:
                # Fallback to raw output
                return CommandExecuteResponse(
                    success=(exit_code == 0),
                    output=output,
                    error=error if error else None,
                    exit_code=exit_code
                )
        finally:
            stdout_capture.close()
            stderr_capture.close()
    
    # Special handling for 'connect update' with connection selection and update data
    if request.command.strip() == "connect update":
        
        # Get the selected connection name (from checkbox-list)
        connection_name = request.params.get("connection_name")
        if isinstance(connection_name, list):
            connection_name = connection_name[0] if connection_name else None
        
        if not connection_name:
            return CommandExecuteResponse(
                success=False,
                output="",
                error="No connection selected",
                exit_code=1
            )
        
        # Update the connection with components directly (no URI building)
        from app.core.connection_ops import ConnectionManager
        
        conn_mgr = ConnectionManager()
        
        # Extract component values from params
        new_name = request.params.get("name")
        host = request.params.get("host")
        port = request.params.get("port")
        username = request.params.get("username")
        password = request.params.get("password")
        database = request.params.get("database")
        auth_source = request.params.get("auth_source")
        description = request.params.get("description")
        
        # Convert port to int if provided
        if port is not None:
            try:
                port = int(port)
            except (ValueError, TypeError):
                return CommandExecuteResponse(
                    success=False,
                    output="",
                    error=f"Invalid port value: {port}",
                    exit_code=1
                )
        
        # Perform update with components
        success = conn_mgr.update_connection(
            name=connection_name,
            new_name=new_name if new_name != connection_name else None,
            host=host,
            port=port,
            username=username,
            password=password,
            database=database,
            auth_source=auth_source,
            description=description
        )
        
        if not success:
            error_msg = f"Failed to update connection '{connection_name}'"
            # Check if it's due to duplicate name
            if new_name and new_name != connection_name:
                existing = conn_mgr.get_connection(new_name)
                if existing:
                    error_msg = f"Connection name '{new_name}' already exists"
            
            return CommandExecuteResponse(
                success=False,
                output="",
                error=error_msg,
                exit_code=1
            )
        
        # Success message
        display_name = new_name if new_name else connection_name
        output_msg = f"✓ Connection '{display_name}' updated successfully"
        
        return CommandExecuteResponse(
            success=True,
            output=output_msg,
            error=None,
            exit_code=0
        )
    
    # Special handling for 'backup folder add' with connection selection and folder configuration
    if request.command.strip() == "backup folder add":
        
        # Get the selected connection name (from step 1)
        connection_name = request.params.get("connection_name")
        if isinstance(connection_name, list):
            connection_name = connection_name[0] if connection_name else None
        
        if not connection_name:
            return CommandExecuteResponse(
                success=False,
                output="",
                error="No connection selected",
                exit_code=1
            )
        
        # Get folder configuration (from step 2)
        folder_path = request.params.get("folder_path")
        create_if_missing = request.params.get("create_if_missing", True)
        
        if not folder_path:
            return CommandExecuteResponse(
                success=False,
                output="",
                error="Folder path is required",
                exit_code=1
            )
        
        # Add backup folder using ConnectionManager directly
        from app.core.connection_ops import ConnectionManager
        from pathlib import Path
        import os
        
        conn_mgr = ConnectionManager()
        
        # Verify connection exists
        connection = conn_mgr.get_connection(connection_name)
        if not connection:
            return CommandExecuteResponse(
                success=False,
                output="",
                error=f"Connection '{connection_name}' not found",
                exit_code=1
            )
        
        # Process folder path — enforce base dir + suffix (same logic as forms.py)
        from app.core.utils.config import BACKUP_BASE_DIR, BACKUP_FOLDER_SUFFIX
        clean_path = folder_path.strip().strip('/')
        if clean_path.startswith(BACKUP_BASE_DIR):
            clean_path = clean_path[len(BACKUP_BASE_DIR):].strip('/')
        folder_path_base = f"{BACKUP_BASE_DIR}/{clean_path}"
        if not folder_path_base.endswith(BACKUP_FOLDER_SUFFIX):
            folder_path = f"{folder_path_base}{BACKUP_FOLDER_SUFFIX}"
        else:
            folder_path = folder_path_base

        path_obj = Path(folder_path)
        
        # Check if path exists
        if not path_obj.exists():
            if create_if_missing:
                try:
                    path_obj.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    return CommandExecuteResponse(
                        success=False,
                        output="",
                        error=f"Failed to create directory: {str(e)}",
                        exit_code=1
                    )
            else:
                return CommandExecuteResponse(
                    success=False,
                    output="",
                    error=f"Path '{folder_path}' does not exist",
                    exit_code=1
                )
        
        # Check if writable
        if not os.access(folder_path, os.W_OK):
            return CommandExecuteResponse(
                success=False,
                output="",
                error=f"Path is not writable: {folder_path}",
                exit_code=1
            )
        
        # Add to connection
        if conn_mgr.add_backup_path(connection_name, folder_path):
            output_msg = f"✓ Added backup folder: {folder_path}"
            
            return CommandExecuteResponse(
                success=True,
                output=output_msg,
                error=None,
                exit_code=0
            )
        else:
            return CommandExecuteResponse(
                success=False,
                output="",
                error="Folder already exists in connection's backup folder list",
                exit_code=1
            )
    
    # Special handling for 'backup create' with connection and backup configuration
    if request.command.strip() == "backup create":
        
        # Get parameters
        connection_name = request.params.get("connection_name")
        backup_name = request.params.get("backup_name")
        backup_location = request.params.get("backup_location")
        
        if not connection_name:
            return CommandExecuteResponse(
                success=False,
                output="",
                error="Connection name is required",
                exit_code=1
            )
        
        if not backup_name:
            return CommandExecuteResponse(
                success=False,
                output="",
                error="Backup name is required",
                exit_code=1
            )
        
        if not backup_location:
            return CommandExecuteResponse(
                success=False,
                output="",
                error="Backup location is required",
                exit_code=1
            )
        
        # Create backup using BackupManager directly
        from app.core.connection_ops import ConnectionManager
        from app.core.backup_ops import BackupManager
        from pathlib import Path
        
        conn_mgr = ConnectionManager()
        
        # Get connection
        connection = conn_mgr.get_connection(connection_name)
        if not connection:
            return CommandExecuteResponse(
                success=False,
                output="",
                error=f"Connection '{connection_name}' not found",
                exit_code=1
            )
        
        # Verify backup_location is in the connection's backup_paths
        backup_paths = connection.get("backup_paths", [])
        if backup_location not in backup_paths:
            return CommandExecuteResponse(
                success=False,
                output="",
                error=f"Invalid backup location. Must be one of the configured backup folders.",
                exit_code=1
            )
        
        # Build URI from connection components
        connection_uri = conn_mgr.repository.build_uri_from_connection(connection)
        
        # Create backup
        backup_mgr = BackupManager(Path(backup_location))
        
        try:
            backup_path = backup_mgr.create_backup(
                connection_uri,
                connection_name,
                backup_name
            )
            
            return CommandExecuteResponse(
                success=True,
                output=f"✓ Backup '{backup_name}' created successfully at {backup_path}",
                error=None,
                exit_code=0
            )
        except ValueError as e:
            # Duplicate backup name or invalid name
            return CommandExecuteResponse(
                success=False,
                output="",
                error=str(e),
                exit_code=1
            )
        except Exception as e:
            # mongodump failed
            return CommandExecuteResponse(
                success=False,
                output="",
                error=f"Backup failed: {str(e)}",
                exit_code=1
            )
    
    # Special handling for 'backup restore' with backup and connection configuration
    if request.command.strip() == "backup restore":
        
        # Get parameters
        backup_selector = request.params.get("backup_selector")
        connection_name = request.params.get("connection_name")
        drop_collections = request.params.get("drop_collections", False)
        confirmation = request.params.get("confirmation", False)
        
        if not backup_selector:
            return CommandExecuteResponse(
                success=False,
                output="",
                error="Backup selector is required",
                exit_code=1
            )
        
        if not connection_name:
            return CommandExecuteResponse(
                success=False,
                output="",
                error="Connection name is required",
                exit_code=1
            )
        
        if not confirmation:
            return CommandExecuteResponse(
                success=False,
                output="",
                error="You must confirm the restore operation",
                exit_code=1
            )
        
        # Parse composite key: folder_path|backup_name
        try:
            folder_path, backup_name = backup_selector.split("|", 1)
        except ValueError:
            return CommandExecuteResponse(
                success=False,
                output="",
                error="Invalid backup selector format",
                exit_code=1
            )
        
        # Restore backup using BackupManager directly
        from app.core.connection_ops import ConnectionManager
        from app.core.backup_ops import BackupManager
        from pathlib import Path
        
        conn_mgr = ConnectionManager()
        
        # Get backup info
        backup_mgr = BackupManager(Path(folder_path))
        backups = backup_mgr.list_backups()
        backup_info = next((b for b in backups if b.get("backup_name", b["name"]) == backup_name), None)
        
        if not backup_info:
            return CommandExecuteResponse(
                success=False,
                output="",
                error=f"Backup '{backup_name}' not found",
                exit_code=1
            )
        
        backup_path = backup_info["path"]
        
        # Get connection and build URI
        connection = conn_mgr.get_connection(connection_name)
        if not connection:
            return CommandExecuteResponse(
                success=False,
                output="",
                error=f"Connection '{connection_name}' not found",
                exit_code=1
            )
        
        connection_uri = conn_mgr.repository.build_uri_from_connection(connection)
        
        # Perform restore
        try:
            backup_mgr.restore_backup(backup_path, connection_uri, drop_collections)
            
            drop_msg = " (with --drop flag)" if drop_collections else ""
            return CommandExecuteResponse(
                success=True,
                output=f"✓ Backup '{backup_name}' restored successfully to '{connection_name}'{drop_msg}",
                error=None,
                exit_code=0
            )
        except Exception as e:
            return CommandExecuteResponse(
                success=False,
                output="",
                error=f"Restore failed: {str(e)}",
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
            # Convert underscores to dashes for CLI compatibility (e.g., auth_source -> auth-source)
            cli_key = key.replace("_", "-")
            cmd_parts.append(f"--{cli_key}")
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
