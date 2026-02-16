"""HTTP API endpoints for form management"""

from fastapi import APIRouter, HTTPException, Depends
from app.core.form_definitions import CONNECT_ADD_FORM
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/forms", tags=["forms"])

# Registry mapping command paths to form schemas
FORM_REGISTRY = {
    "connect/add": CONNECT_ADD_FORM,
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
        command_path: Command path (e.g., "connect/add", "backup/create")
        
    Returns:
        Form schema as JSON
        
    Examples:
        GET /api/forms/connect/add -> Returns CONNECT_ADD_FORM schema
        GET /api/forms/backup/create -> Returns BACKUP_CREATE_FORM schema
        
    Raises:
        404: If no form exists for the given command
    """
    if command_path not in FORM_REGISTRY:
        raise HTTPException(
            status_code=404, 
            detail=f"No form available for command: {command_path}"
        )
    
    form_schema = FORM_REGISTRY[command_path]
    
    # Convert Pydantic model to dict for JSON response
    return form_schema.dict(exclude_none=True)
