"""WebSocket terminal handler for real-time command execution"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from datetime import datetime
import asyncio
import json
import sys
import io
from contextlib import redirect_stdout, redirect_stderr

from app.middleware.auth import verify_token
from app.core.cli import app as cli_app

router = APIRouter()


@router.websocket("/ws/terminal")
async def terminal_websocket(
    websocket: WebSocket,
    token: str = Query(...)
):
    """WebSocket endpoint for real-time command execution
    
    Client sends: {"type": "execute", "command": "connect list"}
    Server sends: {"type": "output", "line": "...", "timestamp": "..."}
                  {"type": "complete", "status": "success", "exit_code": 0}
                  {"type": "error", "message": "...", "exit_code": 1}
    """
    # Verify authentication
    try:
        user = verify_token(token)
    except Exception as e:
        await websocket.close(code=1008, reason="Unauthorized")
        return
    
    await websocket.accept()
    
    try:
        while True:
            # Receive command from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") != "execute":
                continue
            
            command = message.get("command", "")
            if not command:
                continue
            
            # Execute command and stream output
            await execute_command_and_stream(websocket, command)
            
    except WebSocketDisconnect:
        print(f"Client {user.get('username')} disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass


async def execute_command_and_stream(websocket: WebSocket, command: str):
    """Execute CLI command and stream output line by line
    
    Args:
        websocket: WebSocket connection
        command: Command string to execute
    """
    try:
        # Parse command (remove "mongodb-manager" prefix if present)
        cmd_parts = command.strip().split()
        if cmd_parts and cmd_parts[0] == "mongodb-manager":
            cmd_parts = cmd_parts[1:]
        
        if not cmd_parts:
            await websocket.send_json({
                "type": "error",
                "message": "Empty command"
            })
            return
        
        # Capture stdout and stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        # Execute command using Typer CLI
        exit_code = 0
        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                # Invoke the CLI app with the command parts
                cli_app(cmd_parts, standalone_mode=False)
        except SystemExit as e:
            exit_code = e.code if e.code is not None else 0
        except Exception as e:
            exit_code = 1
            stderr_capture.write(str(e))
        
        # Get output
        stdout_value = stdout_capture.getvalue()
        stderr_value = stderr_capture.getvalue()
        
        # Stream stdout line by line
        if stdout_value:
            for line in stdout_value.splitlines():
                await websocket.send_json({
                    "type": "output",
                    "line": line,
                    "timestamp": datetime.utcnow().isoformat()
                })
                await asyncio.sleep(0.01)  # Small delay for smooth streaming
        
        # Stream stderr if any
        if stderr_value:
            for line in stderr_value.splitlines():
                await websocket.send_json({
                    "type": "output",
                    "line": f"ERROR: {line}",
                    "timestamp": datetime.utcnow().isoformat()
                })
                await asyncio.sleep(0.01)
        
        # Send completion message
        await websocket.send_json({
            "type": "complete",
            "status": "success" if exit_code == 0 else "error",
            "exit_code": exit_code
        })
        
    except Exception as e:
        # Send error message
        await websocket.send_json({
            "type": "error",
            "message": str(e),
            "exit_code": 1
        })
