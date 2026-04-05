"""Transfer router — backup export/import and connection export/import endpoints.

All four operations bypass the generic form/command system and use dedicated
REST endpoints because they require file streaming (download) or multipart
file uploads, which the JSON-based form system cannot handle.
"""

import io
import json
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.core.backup_ops import BackupManager
from app.core.connection_ops import ConnectionManager
from app.core.utils.backup_utils import collect_all_backups, parse_backup_selector
from app.middleware.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/transfer", tags=["transfer"])


# ─────────────────────────────────────────────────────────────────────────────
# Options endpoints (used by the frontend widget to populate dropdowns)
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/backup/export/options")
async def backup_export_options(
    current_user: dict = Depends(get_current_user),
):
    """Return all available backups as selector options for the export widget.

    Returns:
        { "backups": [{"value": "folder|name", "label": "...", "description": "..."}] }
    """
    conn_mgr = ConnectionManager()
    connections = conn_mgr.list_connections()
    all_backups = collect_all_backups(connections)

    options = []
    for backup in sorted(
        all_backups, key=lambda b: b.get("created_at", ""), reverse=True
    ):
        composite_key = f"{backup['folder_path']}|{backup['backup_name']}"
        options.append(
            {
                "value": composite_key,
                "label": f"{backup['backup_name']} ({backup['connection_name']})",
                "description": f"Created: {backup.get('created_at', '')}",
            }
        )

    return {"backups": options}


@router.get("/backup/import/options")
async def backup_import_options(
    current_user: dict = Depends(get_current_user),
):
    """Return all registered backup folders as options for the import widget.

    Returns:
        { "folders": [{"value": "/path/to/folder", "label": "..."}] }
    """
    conn_mgr = ConnectionManager()
    connections = conn_mgr.list_connections()

    seen: set[str] = set()
    folders = []
    for conn in connections:
        for path in conn.get("backup_paths", []):
            if path not in seen:
                seen.add(path)
                folders.append({"value": path, "label": path})

    folders.sort(key=lambda x: x["label"])
    return {"folders": folders}


# ─────────────────────────────────────────────────────────────────────────────
# Backup export  (GET → ZIP download)
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/backup/export")
async def export_backup(
    backup_selector: str,
    current_user: dict = Depends(get_current_user),
):
    """Stream a backup folder as a ZIP file download.

    Query params:
        backup_selector: composite key ``folder_path|backup_name``

    Returns:
        StreamingResponse with Content-Disposition: attachment; filename="<backup_name>.zip"
    """
    try:
        folder_path, backup_name = parse_backup_selector(backup_selector)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid backup_selector format")

    backup_mgr = BackupManager(Path(folder_path))

    try:
        zip_bytes = backup_mgr.export_backup_zip(backup_name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error during backup export")
        raise HTTPException(status_code=500, detail=f"Export failed: {exc}")

    filename = f"{backup_name}.zip"
    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ─────────────────────────────────────────────────────────────────────────────
# Backup import  (POST multipart → extract into folder)
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/backup/import")
async def import_backup(
    file: UploadFile,
    folder_path: str = Form(...),
    overwrite: bool = Form(False),
    current_user: dict = Depends(get_current_user),
):
    """Import a ZIP file into a registered backup folder.

    Form fields:
        file: The ZIP file to upload
        folder_path: Destination backup folder (must be a registered folder)
        overwrite: Replace existing backup with the same name (default False)

    Returns:
        { "success": true, "message": "...", "backup_name": "..." }
    """
    if not folder_path:
        raise HTTPException(status_code=400, detail="folder_path is required")

    # Validate that the folder is a registered backup folder
    conn_mgr = ConnectionManager()
    connections = conn_mgr.list_connections()
    all_paths: set[str] = set()
    for conn in connections:
        for p in conn.get("backup_paths", []):
            all_paths.add(p)

    if folder_path not in all_paths:
        raise HTTPException(
            status_code=400,
            detail=(
                f"'{folder_path}' is not a registered backup folder. "
                "Register it first with 'backup folder add'."
            ),
        )

    try:
        zip_bytes = await file.read()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded file: {exc}")

    backup_mgr = BackupManager(Path(folder_path))

    try:
        backup_name = backup_mgr.import_backup_zip(zip_bytes, overwrite=overwrite)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error during backup import")
        raise HTTPException(status_code=500, detail=f"Import failed: {exc}")

    return {
        "success": True,
        "message": f"Backup '{backup_name}' imported successfully into '{folder_path}'",
        "backup_name": backup_name,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Connection export  (GET → JSON download)
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/connect/export")
async def export_connections(
    current_user: dict = Depends(get_current_user),
):
    """Stream all connections as a JSON file download (passwords excluded).

    Returns:
        StreamingResponse with Content-Disposition: attachment; filename="connections.json"
    """
    conn_mgr = ConnectionManager()

    try:
        connections = conn_mgr.export_connections()
    except Exception as exc:
        logger.exception("Unexpected error during connection export")
        raise HTTPException(status_code=500, detail=f"Export failed: {exc}")

    payload = json.dumps({"connections": connections}, indent=2, default=str)
    json_bytes = payload.encode("utf-8")

    return StreamingResponse(
        io.BytesIO(json_bytes),
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="connections.json"'},
    )


# ─────────────────────────────────────────────────────────────────────────────
# Connection import  (POST multipart → parse JSON + insert/update)
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/connect/import")
async def import_connections(
    file: UploadFile,
    overwrite: bool = Form(False),
    import_backup_paths: bool = Form(False),
    current_user: dict = Depends(get_current_user),
):
    """Import connections from a JSON file.

    The JSON file must have the structure produced by the export endpoint::

        { "connections": [ { "name": "...", "host": "...", ... } ] }

    Form fields:
        file: The JSON file to upload
        overwrite: Replace existing connections with the same name (default False)
        import_backup_paths: Preserve backup_paths from the file (default False)

    Returns:
        {
            "success": true,
            "imported": <int>,
            "overwritten": <int>,
            "skipped": <int>,
            "errors": [<str>]
        }
    """
    try:
        raw_bytes = await file.read()
        payload = json.loads(raw_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid JSON file: {exc}",
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded file: {exc}")

    connections = payload.get("connections")
    if not isinstance(connections, list):
        raise HTTPException(
            status_code=400,
            detail="JSON must have a top-level 'connections' array",
        )

    if not connections:
        return {
            "success": True,
            "imported": 0,
            "overwritten": 0,
            "skipped": 0,
            "errors": [],
            "message": "No connections found in file",
        }

    conn_mgr = ConnectionManager()

    try:
        result = conn_mgr.import_connections(
            connections=connections,
            overwrite=overwrite,
            import_backup_paths=import_backup_paths,
        )
    except Exception as exc:
        logger.exception("Unexpected error during connection import")
        raise HTTPException(status_code=500, detail=f"Import failed: {exc}")

    parts = []
    if result["imported"]:
        parts.append(f"{result['imported']} imported")
    if result["overwritten"]:
        parts.append(f"{result['overwritten']} overwritten")
    if result["skipped"]:
        parts.append(f"{result['skipped']} skipped")

    message = ", ".join(parts) if parts else "No changes made"
    if result["errors"]:
        message += f" ({len(result['errors'])} error(s))"

    return {
        "success": True,
        "message": message,
        **result,
    }
