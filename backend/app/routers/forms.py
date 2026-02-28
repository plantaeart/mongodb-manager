"""HTTP API endpoints for form management"""

from fastapi import APIRouter, HTTPException, Depends
from app.core.form_definitions import (
    CONNECT_ADD_FORM, 
    CONNECT_REMOVE_FORM, 
    CONNECT_LIST_FORM, 
    CONNECT_TEST_FORM,
    CONNECT_UPDATE_SELECT_FORM,
    CONNECT_UPDATE_DETAILS_FORM
)
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/forms", tags=["forms"])

# Registry mapping command paths to form schemas
FORM_REGISTRY = {
    "connect/add": CONNECT_ADD_FORM,
    "connect/remove": CONNECT_REMOVE_FORM,
    "connect/list": CONNECT_LIST_FORM,
    "connect/test": CONNECT_TEST_FORM,
    "connect/update/select": CONNECT_UPDATE_SELECT_FORM,
    "connect/update/details": CONNECT_UPDATE_DETAILS_FORM,
    # Add more form commands here as needed
    # "backup/create": BACKUP_CREATE_FORM,
    # "mongodb/discover": MONGODB_DISCOVER_FORM,
}


@router.get("/connection-details/{connection_name}")
async def get_connection_details(
    connection_name: str,
    current_user: dict = Depends(get_current_user)
):
    """Get connection details for pre-populating update form (Step 2)
    
    Args:
        connection_name: Name of the connection to fetch
        
    Returns:
        Connection details with parsed URI components
        
    Raises:
        404: If connection not found
    """
    from app.core.connection_ops import ConnectionManager
    from urllib.parse import urlparse, parse_qs
    import re
    
    conn_mgr = ConnectionManager()
    connection = conn_mgr.get_connection(connection_name)
    
    if not connection:
        raise HTTPException(
            status_code=404,
            detail=f"Connection '{connection_name}' not found"
        )
    
    # Parse URI to extract components for Advanced mode
    uri = connection.get("uri", "")
    parsed = urlparse(uri)
    
    # Extract username and password
    username = parsed.username or ""
    password = parsed.password or ""
    
    # Extract host and port
    host = parsed.hostname or "localhost"
    port = parsed.port or 27017
    
    # Extract database from path
    database = parsed.path.lstrip("/") if parsed.path else ""
    
    # Extract auth_source from query params
    query_params = parse_qs(parsed.query)
    auth_source = query_params.get("authSource", ["admin"])[0]
    
    return {
        "name": connection.get("name", ""),
        "uri": uri,
        "description": connection.get("description", ""),
        "host": host,
        "port": port,
        "username": username,
        "password": password,
        "database": database,
        "auth_source": auth_source
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
    
    # Special handling for connect/test: populate connection options for checkbox-list
    if command_path == "connect/test":
        from app.core.connection_ops import ConnectionManager
        from app.core.utils.uri_builder import mask_password_in_uri
        
        conn_mgr = ConnectionManager()
        connections = conn_mgr.list_connections()
        
        form_dict = form_schema.dict(exclude_none=True)
        
        # Build options from connections
        options = []
        for conn in connections:
            uri_display = mask_password_in_uri(conn["uri"])
            desc = conn.get("description", "")
            
            options.append({
                "value": conn["name"],
                "label": conn["name"],
                "description": desc or uri_display,
                "metadata": {
                    "uri": uri_display,
                    "description": desc
                }
            })
        
        # Update the checkbox-list field with options
        for field in form_dict.get("fields", []):
            if field["id"] == "connections":
                field["options"] = options
                break
        
        return form_dict
    
    # Special handling for connect/update/select: populate connection options for Step 1
    if command_path == "connect/update/select":
        from app.core.connection_ops import ConnectionManager
        from app.core.utils.uri_builder import mask_password_in_uri
        
        conn_mgr = ConnectionManager()
        connections = conn_mgr.list_connections()
        
        form_dict = form_schema.dict(exclude_none=True)
        
        # Build connection options for selector
        options = []
        for conn in connections:
            uri_display = mask_password_in_uri(conn["uri"])
            desc = conn.get("description", "")
            
            options.append({
                "value": conn["name"],
                "label": conn["name"],
                "description": desc or uri_display,
                "metadata": {
                    "uri": uri_display,
                    "description": desc
                }
            })
        
        # Populate connection selector options
        for field in form_dict.get("fields", []):
            if field["id"] == "connection_name":
                field["options"] = options
                break
        
        return form_dict
    
    # Special handling for connect/update/details: Step 2 form (no dynamic data needed here)
    if command_path == "connect/update/details":
        # This form will be pre-populated by frontend when connection is selected
        return form_schema.dict(exclude_none=True)
    
    # Convert Pydantic model to dict for JSON response
    return form_schema.dict(exclude_none=True)
