"""Connect form GET population helpers"""

from datetime import datetime

from app.core.utils.uri_builder import build_mongodb_uri_masked


def build_connection_options_with_date(connections: list[dict]) -> list[dict]:
    """Build checkbox-list / select options with masked URI and formatted date metadata."""
    options = []
    for conn in connections:
        uri_display = build_mongodb_uri_masked(
            host=conn.get("host", "localhost"),
            port=conn.get("port", 27017),
            username=conn.get("username"),
            database=conn.get("database"),
            auth_source=conn.get("auth_source", "admin"),
        )
        desc = conn.get("description", "")
        added_at = conn.get("added_at", "")

        date_display = ""
        if added_at:
            try:
                dt = datetime.fromisoformat(added_at.replace("Z", "+00:00"))
                date_display = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                date_display = added_at

        options.append({
            "value": conn["name"],
            "label": conn["name"],
            "description": desc or uri_display,
            "metadata": {
                "uri": uri_display,
                "description": desc,
                "added_at": date_display,
            },
        })
    return options


def build_connection_options(connections: list[dict]) -> list[dict]:
    """Build select options with masked URI (no date metadata)."""
    options = []
    for conn in connections:
        uri_display = build_mongodb_uri_masked(
            host=conn.get("host", "localhost"),
            port=conn.get("port", 27017),
            username=conn.get("username"),
            database=conn.get("database"),
            auth_source=conn.get("auth_source", "admin"),
        )
        desc = conn.get("description", "")
        options.append({
            "value": conn["name"],
            "label": conn["name"],
            "description": desc or uri_display,
            "metadata": {
                "uri": uri_display,
                "description": desc,
            },
        })
    return options


def build_connection_list_items(connections: list[dict]) -> list[dict]:
    """Build list items for the connection list display."""
    items = []
    for conn in connections:
        masked_uri = build_mongodb_uri_masked(
            host=conn.get("host", "localhost"),
            port=conn.get("port", 27017),
            username=conn.get("username"),
            database=conn.get("database"),
            auth_source=conn.get("auth_source", "admin"),
        )
        items.append({
            "name": conn["name"],
            "uri": masked_uri,
            "description": conn.get("description", ""),
            "added_at": conn.get("added_at", ""),
        })
    return items
