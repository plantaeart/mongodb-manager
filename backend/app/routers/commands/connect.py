"""Connect command handlers"""

import io
import json
from contextlib import redirect_stdout, redirect_stderr

from app.core.connection_ops import ConnectionManager
from app.routers.commands.models import CommandExecuteResponse


def handle_connect_remove(cli_app, connections_to_remove: list) -> CommandExecuteResponse:
    """Remove one or more connections by name"""
    failed_count = 0
    all_output: list[str] = []
    all_errors: list[str] = []

    for conn_name in connections_to_remove:
        single_cmd_parts = ["connect", "remove", "--name", conn_name, "--yes"]

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

            if single_exit_code != 0:
                failed_count += 1
                all_errors.append(single_stderr.getvalue())
            else:
                all_output.append(single_stdout.getvalue())
        finally:
            single_stdout.close()
            single_stderr.close()

    success_count = len(connections_to_remove) - failed_count
    combined_output = "\n".join(all_output)
    combined_errors = "\n".join(all_errors)

    if success_count > 0:
        combined_output += f"\n✓ Successfully removed {success_count} connection(s)"
    if failed_count > 0:
        combined_errors += f"\n✗ Failed to remove {failed_count} connection(s)"

    return CommandExecuteResponse(
        success=(failed_count == 0),
        output=combined_output,
        error=combined_errors if combined_errors else None,
        exit_code=0 if failed_count == 0 else 1,
    )


def handle_connect_test(cli_app, connections_to_test: list) -> CommandExecuteResponse:
    """Test one or more connections and return formatted results"""
    names_param = ",".join(connections_to_test)
    cmd_parts = ["connect", "test", "--names", names_param, "--yes", "--json"]

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

        try:
            result_data = json.loads(output)
            results = result_data.get("results", [])
            summary = result_data.get("summary", {})

            formatted_lines: list[str] = []
            formatted_lines.append(f"Testing {summary.get('total', 0)} connection(s):")
            formatted_lines.append("")

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
                formatted_lines.append("")

            formatted_lines.append(
                f"Summary: {summary.get('success', 0)} successful, {summary.get('failure', 0)} failed"
            )

            return CommandExecuteResponse(
                success=(exit_code == 0),
                output="\n".join(formatted_lines),
                error=error if error else None,
                exit_code=exit_code,
            )
        except json.JSONDecodeError:
            return CommandExecuteResponse(
                success=(exit_code == 0),
                output=output,
                error=error if error else None,
                exit_code=exit_code,
            )
    finally:
        stdout_capture.close()
        stderr_capture.close()


def handle_connect_update(params: dict) -> CommandExecuteResponse:
    """Update an existing connection using component fields"""
    connection_name = params.get("connection_name")
    if isinstance(connection_name, list):
        connection_name = connection_name[0] if connection_name else None

    if not connection_name:
        return CommandExecuteResponse(
            success=False, output="", error="No connection selected", exit_code=1
        )

    new_name = params.get("name")
    host = params.get("host")
    port = params.get("port")
    username = params.get("username")
    password = params.get("password")
    database = params.get("database")
    auth_source = params.get("auth_source")
    description = params.get("description")

    if port is not None:
        try:
            port = int(port)
        except (ValueError, TypeError):
            return CommandExecuteResponse(
                success=False,
                output="",
                error=f"Invalid port value: {port}",
                exit_code=1,
            )

    conn_mgr = ConnectionManager()
    success = conn_mgr.update_connection(
        name=connection_name,
        new_name=new_name if new_name != connection_name else None,
        host=host,
        port=port,
        username=username,
        password=password,
        database=database,
        auth_source=auth_source,
        description=description,
    )

    if not success:
        error_msg = f"Failed to update connection '{connection_name}'"
        if new_name and new_name != connection_name:
            existing = conn_mgr.get_connection(new_name)
            if existing:
                error_msg = f"Connection name '{new_name}' already exists"
        return CommandExecuteResponse(
            success=False, output="", error=error_msg, exit_code=1
        )

    display_name = new_name if new_name else connection_name
    return CommandExecuteResponse(
        success=True,
        output=f"✓ Connection '{display_name}' updated successfully",
        error=None,
        exit_code=0,
    )
