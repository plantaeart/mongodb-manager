"""HTTP API endpoints for form management"""

from fastapi import APIRouter, HTTPException, Depends
from app.core.form_definitions import CONNECT_ADD_FORM, CONNECT_REMOVE_FORM, CONNECT_LIST_FORM
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/forms", tags=["forms"])

# Registry mapping command paths to form schemas
FORM_REGISTRY = {
    "connect/add": CONNECT_ADD_FORM,
    "connect/remove": CONNECT_REMOVE_FORM,
    "connect/list": CONNECT_LIST_FORM,
    # Add more form commands here as needed
    # "backup/create": BACKUP_CREATE_FORM,
    # "mongodb/discover": MONGODB_DISCOVER_FORM,
}


@router.get("/{command_path:path}")
async def get_form_schema(
    command_path: str,
    current_user: dict = Depends(get_current_user)
):
    """Get form schema for a command
    
    Args:
        command_path: Command path (e.g., "connect/add", "connect/remove")
        
    Returns:
        Form schema as JSON
        
    Examples:
        GET /api/forms/connect/add -> Returns CONNECT_ADD_FORM schema
        GET /api/forms/connect/remove -> Returns CONNECT_REMOVE_FORM with populated connections
        
    Raises:
        404: If no form exists for the given command
    """
    if command_path not in FORM_REGISTRY:
        raise HTTPException(
            status_code=404, 
            detail=f"No form available for command: {command_path}"
        )
    
    form_schema = FORM_REGISTRY[command_path]
    
    # Special handling for connect/remove: populate connection options dynamically
    if command_path == "connect/remove":
        from app.core.connection_ops import ConnectionManager
        from app.core.utils.uri_builder import mask_password_in_uri
        from datetime import datetime
        
        conn_mgr = ConnectionManager()
        connections = conn_mgr.list_connections()
        
        # Build options from connections
        options = []
        for conn in connections:
            uri_display = mask_password_in_uri(conn["uri"])
            desc = conn.get("description", "")
            added_at = conn.get("added_at", "")
            
            # Format added_at if available
            date_display = ""
            if added_at:
                try:
                    dt = datetime.fromisoformat(added_at.replace("Z", "+00:00"))
                    date_display = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    date_display = added_at
            
            options.append({
                "value": conn["name"],
                "label": conn["name"],
                "description": desc or uri_display,
                "metadata": {
                    "uri": uri_display,
                    "description": desc,
                    "added_at": date_display
                }
            })
        
        # Create a copy of the form schema and populate options
        form_dict = form_schema.dict(exclude_none=True)
        
        # Find the connections field and populate options
        for field in form_dict.get("fields", []):
            if field["id"] == "connections":
                field["options"] = options
                break
        
        return form_dict
    
    # Special handling for connect/list: populate connection items
    if command_path == "connect/list":
        from app.core.connection_ops import ConnectionManager
        from app.core.utils.uri_builder import mask_password_in_uri
        
        conn_mgr = ConnectionManager()
        connections = conn_mgr.list_connections()
        
        # Create a copy of the form schema
        form_dict = form_schema.dict(exclude_none=True)
        
        # Build items array with connection data
        items = []
        for conn in connections:
            items.append({
                "name": conn["name"],
                "uri": mask_password_in_uri(conn["uri"]),
                "description": conn.get("description", ""),
                "added_at": conn.get("added_at", "")
            })
        
        # Update the list field with items
        for field in form_dict.get("fields", []):
            if field["id"] == "connections_list":
                field["items"] = items
                break
        
        return form_dict
    
    # Convert Pydantic model to dict for JSON response
    return form_schema.dict(exclude_none=True)
