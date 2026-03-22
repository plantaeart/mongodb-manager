"""HTTP API endpoints for command execution"""

import io
import logging
from contextlib import redirect_stdout, redirect_stderr
from typing import Callable

from fastapi import APIRouter, Depends

from app.core.cli import app as cli_app
from app.middleware.auth import get_current_user
from app.enums import Command
from app.routers.commands.models import CommandExecuteRequest, CommandExecuteResponse
from app.routers.commands.connect import (
    handle_connect_remove,
    handle_connect_test,
    handle_connect_update,
)
from app.routers.commands.backup_folder import (
    handle_backup_folder_add,
    handle_backup_folder_delete,
)
from app.routers.commands.backup_ops import handle_backup_create, handle_backup_restore

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/commands", tags=["commands"])


def _make_list_handler(
    handler: Callable, param_key: str, empty_error: str
) -> Callable[[dict], CommandExecuteResponse]:
    """Wrap a multi-item handler (remove / test) with list-coercion and empty-guard logic."""

    def _wrapped(params: dict) -> CommandExecuteResponse:
        items = params.get(param_key, [])
        if not isinstance(items, list):
            items = [items]
        if not items:
            return CommandExecuteResponse(
                success=False, output="", error=empty_error, exit_code=1
            )
        return handler(cli_app, items)

    return _wrapped


# OCP registry — add new commands here without touching execute_command
COMMAND_HANDLERS: dict[Command, Callable[[dict], CommandExecuteResponse]] = {
    Command.CONNECT_REMOVE: _make_list_handler(
        handle_connect_remove, "connections", "No connections selected"
    ),
    Command.CONNECT_TEST: _make_list_handler(
        handle_connect_test, "connections", "No connections selected"
    ),
    Command.CONNECT_UPDATE: lambda params: handle_connect_update(params),
    Command.BACKUP_FOLDER_ADD: lambda params: handle_backup_folder_add(params),
    Command.BACKUP_FOLDER_DELETE: lambda params: handle_backup_folder_delete(params),
    Command.BACKUP_CREATE: lambda params: handle_backup_create(params),
    Command.BACKUP_RESTORE: lambda params: handle_backup_restore(params),
}


def _coerce_port(params: dict) -> CommandExecuteResponse | None:
    """Coerce port param to int; return an error response on failure, None on success."""
    if "port" not in params:
        params["port"] = 27017
        return None

    port_value = params["port"]
    if isinstance(port_value, str):
        if port_value.strip() == "":
            params["port"] = 27017
        else:
            try:
                params["port"] = int(port_value)
            except (ValueError, TypeError):
                return CommandExecuteResponse(
                    success=False,
                    output="",
                    error=f"Invalid port value: {port_value}",
                    exit_code=1,
                )
    elif port_value is None:
        params["port"] = 27017

    return None


def _run_generic_cli(command: str, params: dict) -> CommandExecuteResponse:
    """Execute a raw CLI command via the Typer app (generic fallback)."""
    cmd_parts = command.split()

    for key, value in params.items():
        if key.startswith("_"):
            continue
        if value is not None and value != "":
            cli_key = key.replace("_", "-")
            cmd_parts.append(f"--{cli_key}")
            cmd_parts.append(str(value))

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

        return CommandExecuteResponse(
            success=(exit_code == 0),
            output=output,
            error=error if error else None,
            exit_code=exit_code,
        )

    except Exception as e:
        return CommandExecuteResponse(
            success=False,
            output="",
            error=f"Failed to execute command: {str(e)}",
            exit_code=1,
        )
    finally:
        stdout_capture.close()
        stderr_capture.close()


@router.post("/execute", response_model=CommandExecuteResponse)
async def execute_command(
    request: CommandExecuteRequest,
    current_user: dict = Depends(get_current_user),
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
    command = request.command.strip()

    # Port coercion applies before any handler for connect add / update
    if command in (Command.CONNECT_ADD, Command.CONNECT_UPDATE):
        err = _coerce_port(request.params)
        if err:
            return err

    # Dispatch via registry — look up by enum value, fall back to generic CLI
    try:
        cmd_enum = Command(command)
    except ValueError:
        return _run_generic_cli(command, request.params)

    handler = COMMAND_HANDLERS.get(cmd_enum)
    if handler is None:
        return _run_generic_cli(command, request.params)

    # CONNECT_REMOVE / CONNECT_TEST require the "connections" key to be present;
    # without it, fall through to the generic CLI path.
    if cmd_enum in (Command.CONNECT_REMOVE, Command.CONNECT_TEST):
        if "connections" not in request.params:
            return _run_generic_cli(command, request.params)

    return handler(request.params)
