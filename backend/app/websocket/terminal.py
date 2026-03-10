"""WebSocket terminal handler for command execution"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from datetime import datetime
import asyncio
import json
import sys
import logging
from contextvars import ContextVar
from contextlib import redirect_stdout, redirect_stderr

from app.middleware.auth import verify_token
from app.core.cli import app as cli_app
from app.websocket.forms import FormManager

router = APIRouter()
logger = logging.getLogger("mongodb_manager.websocket")

# Global form manager instance
form_manager = FormManager()

# Context variables for WebSocket and form manager access in CLI commands
_websocket_context: ContextVar[WebSocket | None] = ContextVar('websocket_context', default=None)
_form_manager_context: ContextVar[FormManager | None] = ContextVar('form_manager_context', default=None)


def get_websocket_context() -> WebSocket | None:
    """Get current WebSocket from context (if in WebSocket command execution)"""
    return _websocket_context.get()


def get_form_manager() -> FormManager | None:
    """Get FormManager from context (if in WebSocket command execution)"""
    return _form_manager_context.get()


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
        """Flush any remaining buffer to WebSocket
        
        This ensures any buffered output that doesn't end with newline
        gets sent to the client before command completes.
        """
        if not self._buffer or self._closed or self._writing:
            return
        
        try:
            self._writing = True
            
            # Get event loop
            if self._loop is None:
                try:
                    self._loop = asyncio.get_running_loop()
                except RuntimeError:
                    return
            
            # Send remaining buffer content and WAIT for completion
            if self._buffer:
                try:
                    future = asyncio.run_coroutine_threadsafe(
                        self._send_line(self._buffer),
                        self._loop
                    )
                    # Wait up to 1 second for send to complete
                    future.result(timeout=1.0)
                except Exception:
                    pass
                finally:
                    self._buffer = ""
        
        finally:
            self._writing = False
    
    def isatty(self):
        """Not a TTY"""
        return False
    
    def close(self):
        """Close the stream and flush remaining output"""
        if self._closed:
            return
        
        # Flush any remaining content before closing
        self.flush()
        
        # Mark as closed
        self._closed = True


@router.websocket("/ws/terminal")
async def terminal_websocket(
    websocket: WebSocket,
    token: str = Query(...)
):
    """WebSocket endpoint for command execution
    
    Client sends: {"type": "execute", "command": "connect list"}
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
            
            message_type = message.get("type")
            
            if message_type == "execute":
                command = message.get("command", "")
                if command:
                    await execute_command_and_stream(websocket, command)
            
            elif message_type == "form_submit":
                form_id = message.get("form_id")
                form_data = message.get("data")
                if form_id and form_data is not None:
                    form_manager.handle_form_submit(form_id, form_data)
            
            elif message_type == "form_cancel":
                form_id = message.get("form_id")
                if form_id:
                    form_manager.handle_form_cancel(form_id)
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
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
    # Set context variables for this command execution
    _websocket_context.set(websocket)
    _form_manager_context.set(form_manager)
    
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
        
        # Replace global console AND patch existing console references
        import app.core.ui as ui_module
        import app.core.cli as cli_module
        
        original_console = ui_module.console
        
        # Replace console in ui module
        ui_module.console = websocket_console
        
        # CRITICAL: Also replace in cli module (it imports console directly)
        cli_module.console = websocket_console
        
        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                # CRITICAL FIX: Don't use thread - run CLI directly in this event loop
                # The issue was that threading created a NEW event loop (via anyio.run)
                # which couldn't communicate with our WebSocket event loop's Futures
                
                # Invoke CLI directly - Typer will handle async properly
                # Context vars are already set (lines 200-201)
                cli_app(cmd_parts, standalone_mode=False)
                
        except SystemExit as e:
            exit_code = e.code if e.code is not None else 0
        except Exception as e:
            exit_code = 1
            try:
                stderr_capture.write(str(e) + "\n")
            except:
                pass
        
        # Flush buffers BEFORE restoring console
        stdout_capture.flush()
        stderr_capture.flush()
        await asyncio.sleep(0.05)
        
        # Restore console after flush (both modules)
        ui_module.console = original_console
        cli_module.console = original_console
        
        # Send completion
        await websocket.send_json({
            "type": "complete",
            "status": "success" if exit_code == 0 else "error",
            "exit_code": exit_code
        })
        
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e),
            "exit_code": 1
        })
    finally:
        # Clear context variables
        _websocket_context.set(None)
        _form_manager_context.set(None)
