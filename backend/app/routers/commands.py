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
    
    # Special handling for 'connect remove' with multiple connections
    if request.command.strip() == "connect remove" and "connections" in request.params:
        # connections is an array of connection names to remove
        connections_to_remove = request.params.get("connections", [])
        logger.info(f"[CONNECT REMOVE] Received request with connections: {connections_to_remove}")
        
        if not isinstance(connections_to_remove, list):
            connections_to_remove = [connections_to_remove]
        
        if not connections_to_remove:
            logger.warning("[CONNECT REMOVE] No connections selected")
            return CommandExecuteResponse(
                success=False,
                output="",
                error="No connections selected",
                exit_code=1
            )
        
        # Remove connections one by one and collect results
        all_output = []
        all_errors = []
        failed_count = 0
        
        logger.info(f"[CONNECT REMOVE] Processing {len(connections_to_remove)} connection(s)")
        
        for conn_name in connections_to_remove:
            # Build CLI arguments for single removal with --yes to skip confirmation
            single_cmd_parts = ["connect", "remove", "--name", str(conn_name), "--yes"]
            logger.info(f"[CONNECT REMOVE] Removing connection: {conn_name}")
            logger.debug(f"[CONNECT REMOVE] CLI command: {single_cmd_parts}")
            
            # Capture output for this removal
            single_stdout = io.StringIO()
            single_stderr = io.StringIO()
            single_exit_code = 0
            
            try:
                with redirect_stdout(single_stdout), redirect_stderr(single_stderr):
                    try:
                        cli_app(single_cmd_parts, standalone_mode=False)
                    except SystemExit as e:
                        single_exit_code = e.code if e.code is not None else 0
                        logger.debug(f"[CONNECT REMOVE] CLI exited with code: {single_exit_code}")
                    except Exception as e:
                        single_exit_code = 1
                        logger.error(f"[CONNECT REMOVE] Exception during removal: {str(e)}", exc_info=True)
                        single_stderr.write(f"Error: {str(e)}\n")
                
                stdout_val = single_stdout.getvalue()
                stderr_val = single_stderr.getvalue()
                logger.debug(f"[CONNECT REMOVE] stdout: {stdout_val}")
                logger.debug(f"[CONNECT REMOVE] stderr: {stderr_val}")
                
                if single_exit_code != 0:
                    failed_count += 1
                    all_errors.append(stderr_val)
                    logger.warning(f"[CONNECT REMOVE] Failed to remove {conn_name}")
                else:
                    all_output.append(stdout_val)
                    logger.info(f"[CONNECT REMOVE] Successfully removed {conn_name}")
            
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
        
        logger.info(f"[CONNECT REMOVE] Complete: {success_count} success, {failed_count} failed")
        logger.debug(f"[CONNECT REMOVE] Combined output: {combined_output}")
        logger.debug(f"[CONNECT REMOVE] Combined errors: {combined_errors}")
        
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
        logger.info(f"[CONNECT TEST] Received request with connections: {connections_to_test}")
        
        if not isinstance(connections_to_test, list):
            connections_to_test = [connections_to_test]
        
        if not connections_to_test:
            logger.warning("[CONNECT TEST] No connections selected")
            return CommandExecuteResponse(
                success=False,
                output="",
                error="No connections selected",
                exit_code=1
            )
        
        # Build command with comma-separated names and JSON output flag
        names_param = ",".join(connections_to_test)
        cmd_parts = ["connect", "test", "--names", names_param, "--yes", "--json"]
        
        logger.info(f"[CONNECT TEST] Testing {len(connections_to_test)} connection(s)")
        logger.debug(f"[CONNECT TEST] CLI command: {cmd_parts}")
        
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
            
            logger.info(f"[CONNECT TEST] Complete with exit code: {exit_code}")
            logger.debug(f"[CONNECT TEST] Raw output: {output}")
            
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
                logger.error(f"[CONNECT TEST] Failed to parse JSON output: {e}")
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
