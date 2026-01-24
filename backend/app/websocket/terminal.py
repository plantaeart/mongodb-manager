"""WebSocket terminal handler for command execution"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from datetime import datetime
import asyncio
import json
import sys
import logging
from contextlib import redirect_stdout, redirect_stderr

from app.middleware.auth import verify_token
from app.core.cli import app as cli_app

router = APIRouter()
logger = logging.getLogger("mongodb_manager.websocket")


class WebSocketOutputStream:
    """Custom output stream that sends to WebSocket
    
    Handles synchronous write() calls from Rich/Typer and converts to async WebSocket sends.
    """
    
    def __init__(self, websocket: WebSocket, output_type: str = "output"):
        self.websocket = websocket
        self.output_type = output_type
        self._buffer = ""
        self._writing = False  # Recursion guard
        self._closed = False
        self._loop = None
    
    def write(self, text: str) -> int:
        """Write text to WebSocket"""
        if not text or self._closed or self._writing:
            return len(text) if text else 0
        
        try:
            self._writing = True
            
            # Get event loop
            if self._loop is None:
                try:
                    self._loop = asyncio.get_running_loop()
                except RuntimeError:
                    return len(text)
            
            # Add to buffer
            self._buffer += text
            
            # Send complete lines
            while '\n' in self._buffer:
                line, self._buffer = self._buffer.split('\n', 1)
                try:
                    asyncio.run_coroutine_threadsafe(
                        self._send_line(line), 
                        self._loop
                    )
                except Exception:
                    pass
            
            return len(text)
            
        finally:
            self._writing = False
    
    async def _send_line(self, line: str):
        """Send a line to WebSocket"""
        if self._closed:
            return
            
        try:
            # Filter debug logs - they go to FastAPI logs only
            if "Input is not a terminal" in line or \
               ("Warning:" in line and "fd=" in line) or \
               line.startswith("[CLI-") or \
               line.startswith("[WS-") or \
               line.startswith("[SCAN-"):
                return
            
            prefix = "ERROR: " if self.output_type == "error" else ""
            await self.websocket.send_json({
                "type": "output",
                "line": prefix + line,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception:
            self._closed = True
    
    def flush(self):
        """Flush any remaining buffer"""
        if self._buffer and not self._closed and not self._writing:
            try:
                self._writing = True
                if self._loop:
                    asyncio.run_coroutine_threadsafe(
                        self._send_line(self._buffer), 
                        self._loop
                    )
                self._buffer = ""
            finally:
                self._writing = False
    
    def isatty(self):
        """Not a TTY"""
        return False
    
    def close(self):
        """Mark stream as closed"""
        self._closed = True


@router.websocket("/ws/terminal")
async def terminal_websocket(
    websocket: WebSocket,
    token: str = Query(...)
):
    """WebSocket endpoint for command execution
    
    Client sends: {"type": "execute", "command": "mongodb discover"}
    Server sends: {"type": "output", "line": "...", "timestamp": "..."}
                  {"type": "complete", "status": "success", "exit_code": 0}
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
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "execute":
                command = message.get("command", "")
                if command:
                    await execute_command_and_stream(websocket, command)
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass


async def execute_command_and_stream(websocket: WebSocket, command: str):
    """Execute CLI command and send output to WebSocket
    
    Args:
        websocket: WebSocket connection
        command: Command string to execute
    """
    try:
        # Parse command
        cmd_parts = command.strip().split()
        if cmd_parts and cmd_parts[0] == "mongodb-manager":
            cmd_parts = cmd_parts[1:]
        
        if not cmd_parts:
            await websocket.send_json({
                "type": "error",
                "message": "Empty command"
            })
            return
        
        # Create output streams
        stdout_capture = WebSocketOutputStream(websocket, "output")
        stderr_capture = WebSocketOutputStream(websocket, "error")
        
        exit_code = 0
        
        # Create Rich console for WebSocket
        from rich.console import Console
        websocket_console = Console(
            file=stdout_capture,
            force_terminal=False,
            force_interactive=False,
            no_color=True,
            width=120,
            soft_wrap=False,
            highlight=False
        )
        
        # Replace global console
        import app.core.ui as ui_module
        original_console = ui_module.console
        ui_module.console = websocket_console
        
        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                try:
                    cli_app(cmd_parts, standalone_mode=False)
                finally:
                    ui_module.console = original_console
                
        except SystemExit as e:
            exit_code = e.code if e.code is not None else 0
        except Exception as e:
            exit_code = 1
            try:
                stderr_capture.write(str(e) + "\n")
            except:
                pass
        
        # Flush buffers
        stdout_capture.flush()
        stderr_capture.flush()
        await asyncio.sleep(0.05)
        
        # Send completion
        await websocket.send_json({
            "type": "complete",
            "status": "success" if exit_code == 0 else "error",
            "exit_code": exit_code
        })
        
    except Exception as e:
        logger.error(f"Command execution error: {e}", exc_info=True)
        await websocket.send_json({
            "type": "error",
            "message": str(e),
            "exit_code": 1
        })
