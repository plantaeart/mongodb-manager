"""Form management for WebSocket terminal interactions"""

import asyncio
import uuid
from typing import Any
from fastapi import WebSocket

from app.core.forms.models import FormSchema


class FormManager:
    """Manage WebSocket form interactions"""
    
    def __init__(self):
        self.pending_responses: dict[str, asyncio.Future] = {}
    
    async def request_form(
        self,
        websocket: WebSocket,
        form_schema: FormSchema
    ) -> dict[str, Any] | None:
        """Send form request to client and wait for response
        
        Args:
            websocket: WebSocket connection
            form_schema: Form schema to send
            
        Returns:
            Form data dict if submitted, None if cancelled or timeout
        """
        form_id = str(uuid.uuid4())
        
        # Create future for response
        future = asyncio.Future()
        self.pending_responses[form_id] = future
        
        # Send form to client
        await websocket.send_json({
            "type": "form_request",
            "form_id": form_id,
            **form_schema.model_dump(exclude_none=True)
        })
        
        try:
            # Wait for response (5 minute timeout)
            result = await asyncio.wait_for(future, timeout=300)
            return result
        except asyncio.TimeoutError:
            # Form timed out
            await websocket.send_json({
                "type": "output",
                "line": "[yellow]Form timed out after 5 minutes[/yellow]",
                "timestamp": ""
            })
            return None
        finally:
            # Cleanup
            if form_id in self.pending_responses:
                del self.pending_responses[form_id]
    
    def handle_form_submit(self, form_id: str, data: dict[str, Any]):
        """Handle form submission from client
        
        Args:
            form_id: Form identifier
            data: Submitted form data
        """
        if form_id in self.pending_responses:
            future = self.pending_responses[form_id]
            if not future.done():
                future.set_result(data)
    
    def handle_form_cancel(self, form_id: str):
        """Handle form cancellation from client
        
        Args:
            form_id: Form identifier
        """
        if form_id in self.pending_responses:
            future = self.pending_responses[form_id]
            if not future.done():
                future.set_result(None)
