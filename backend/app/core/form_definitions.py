"""Form schema definitions for WebSocket terminal forms"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field


class ValidationRule(BaseModel):
    """Validation rules for form fields"""
    pattern: Optional[str] = None
    message: str = "Invalid value"
    min: Optional[int | float] = None
    max: Optional[int | float] = None


class SelectOption(BaseModel):
    """Option for select fields"""
    value: str
    label: str
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ListItemField(BaseModel):
    """Configuration for displaying a field in a list item"""
    key: str  # The property key in the item object
    label: str  # Display label for this field
    icon: Optional[str] = None  # Optional emoji icon
    type: Optional[Literal['text', 'date', 'list', 'badge']] = 'text'  # How to render the value
    primary: Optional[bool] = False  # If true, shown in header
    badge_key: Optional[str] = None  # For type='badge', the key to compare for active state


class ListDisplayConfig(BaseModel):
    """Configuration for how to display list items"""
    header_icon: Optional[str] = None  # Icon for the header
    fields: List[ListItemField]  # Fields to display
    count_label: Optional[str] = "item(s)"  # Label for total count


class FormField(BaseModel):
    """Form field definition"""
    id: str
    label: str
    type: Literal['text', 'textarea', 'number', 'select', 'checkbox', 'checkbox-list', 'date', 'readonly', 'password', 'list']
    required: bool = False
    placeholder: Optional[str] = None
    default: Any = None
    validation: Optional[ValidationRule] = None
    help_text: Optional[str] = None
    tooltip: Optional[str] = None  # Tooltip text for info icon
    
    # Type-specific fields
    rows: Optional[int] = None  # textarea
    min: Optional[int | float] = None  # number, date
    max: Optional[int | float] = None  # number, date
    step: Optional[int | float] = None  # number
    options: Optional[List[SelectOption]] = None  # select, checkbox-list
    content: Optional[str] = None  # readonly
    items: Optional[List[Dict[str, Any]]] = None  # list
    list_config: Optional[ListDisplayConfig] = None  # Configuration for list display


class FormAction(BaseModel):
    """Form action button"""
    label: str
    style: Literal['primary', 'secondary', 'danger']
    action: str


class FormSchema(BaseModel):
    """Form schema (supports both single-step and multi-step forms)"""
    title: str
    description: Optional[str] = None
    step: Optional[int] = None  # Step number (1-indexed) for multi-step forms
    total_steps: Optional[int] = None  # Total steps in multi-step flow
    fields: List[FormField]
    actions: List[FormAction]


# === FORM DEFINITIONS ===

# Connection Add Form (Component-based)
CONNECT_ADD_FORM = FormSchema(
    title="Add MongoDB Connection",
    description="Enter connection details",
    fields=[
        # Connection Name
        FormField(
            id="name",
            label="Connection Name",
            type="text",
            required=True,
            placeholder="my-mongodb",
            validation=ValidationRule(
                pattern=r"^[a-zA-Z0-9_-]+$",
                message="Only letters, numbers, - and _ allowed"
            ),
            help_text="Unique name for this connection"
        ),
        
        # Host
        FormField(
            id="host",
            label="Host",
            type="text",
            required=True,
            default="localhost",
            placeholder="localhost or IP address",
            help_text="MongoDB server hostname or IP",
            tooltip="Docker: Use container name (same network) or host.docker.internal"
        ),
        
        # Port
        FormField(
            id="port",
            label="Port",
            type="number",
            required=True,
            default=27017,
            min=1,
            max=65535,
            help_text="MongoDB server port (default: 27017)",
            tooltip="Docker: Use exposed host port (e.g., 27019) for cross-network access"
        ),
        
        # Username
        FormField(
            id="username",
            label="Username (optional)",
            type="text",
            required=False,
            placeholder="admin",
            help_text="Leave empty for no authentication"
        ),
        
        # Password
        FormField(
            id="password",
            label="Password (optional)",
            type="password",
            required=False,
            placeholder="••••••••",
            help_text="Required if username is provided"
        ),
        
        # Auth Source
        FormField(
            id="auth_source",
            label="Authentication Database",
            type="text",
            required=False,
            default="admin",
            placeholder="admin",
            help_text="Database where user credentials are stored",
            tooltip="Usually 'admin' - database where the user was created"
        ),
        
        # Database
        FormField(
            id="database",
            label="Database (optional)",
            type="text",
            required=False,
            placeholder="mydb",
            help_text="Default database to connect to"
        ),
        
        # Description
        FormField(
            id="description",
            label="Description (optional)",
            type="text",
            required=False,
            placeholder="Production database"
        )
    ],
    actions=[
        FormAction(label="Add Connection", style="primary", action="submit"),
        FormAction(label="Cancel", style="secondary", action="cancel")
    ]
)


# Connection Remove Form (Multi-select with checkbox list)
# Note: Options are populated dynamically from ConnectionManager.list_connections()
CONNECT_REMOVE_FORM = FormSchema(
    title="Remove MongoDB Connection(s)",
    description="Select one or more connections to remove. This action cannot be undone.",
    fields=[
        FormField(
            id="connections",
            label="Connections to Remove",
            type="checkbox-list",
            required=True,
            help_text="Select at least one connection to remove",
            options=[]  # Populated dynamically in CLI
        )
    ],
    actions=[
        FormAction(label="Remove Selected", style="danger", action="submit"),
        FormAction(label="Cancel", style="secondary", action="cancel")
    ]
)

# Connection List Form (Read-only display)
# Note: Content is populated dynamically from ConnectionManager.list_connections()
CONNECT_LIST_FORM = FormSchema(
    title="MongoDB Connections",
    description="Configured MongoDB connections",
    fields=[
        FormField(
            id="connections_list",
            label="",
            type="list",
            items=[],  # Populated dynamically with connection objects
            list_config=ListDisplayConfig(
                header_icon="📌",
                fields=[
                    ListItemField(key="name", label="Name", primary=True),
                    ListItemField(key="uri", label="URI", icon="🔗", type="text"),
                    ListItemField(key="description", label="Description", icon="📝", type="text"),
                    ListItemField(key="added_at", label="Added", icon="📅", type="date")
                ],
                count_label="connection(s)"
            )
        )
    ],
    actions=[
        FormAction(label="Close", style="secondary", action="cancel")
    ]
)

# Connection Test Form
# Note: Options are populated dynamically from ConnectionManager.list_connections()
CONNECT_TEST_FORM = FormSchema(
    title="Test MongoDB Connection(s)",
    description="Select connection(s) to test connectivity",
    fields=[
        FormField(
            id="connections",
            label="Select connections to test",
            type="checkbox-list",
            required=True,
            help_text="Select one or more connections to test",
            options=[]  # Populated dynamically
        )
    ],
    actions=[
        FormAction(label="Test Selected", style="primary", action="submit"),
        FormAction(label="Cancel", style="secondary", action="cancel")
    ]
)


# Connection Update - Step 1: Select Connection
# Note: Options are populated dynamically from ConnectionManager.list_connections()
CONNECT_UPDATE_SELECT_FORM = FormSchema(
    title="Select Connection",
    description="Select the connection you want to update",
    step=1,
    total_steps=2,
    fields=[
        FormField(
            id="connection_name",
            label="Select Connection",
            type="checkbox-list",
            required=True,
            help_text="Choose one connection to update",
            options=[]  # Populated dynamically
        )
    ],
    actions=[
        FormAction(label="Next", style="primary", action="submit"),
        FormAction(label="Cancel", style="secondary", action="cancel")
    ]
)


# Connection Update - Step 2: Update Details
# Note: Form fields are pre-populated with existing connection data
CONNECT_UPDATE_DETAILS_FORM = FormSchema(
    title="Update Details",
    description="Modify connection details",
    step=2,
    total_steps=2,
    fields=[
        
        # Connection Name (can be changed to rename)
        FormField(
            id="name",
            label="Connection Name",
            type="text",
            required=True,
            placeholder="my-mongodb",
            validation=ValidationRule(
                pattern=r"^[a-zA-Z0-9_-]+$",
                message="Only letters, numbers, - and _ allowed"
            ),
            help_text="Unique name for this connection"
        ),
        
        # Host
        FormField(
            id="host",
            label="Host",
            type="text",
            required=True,
            default="localhost",
            placeholder="localhost or IP address",
            help_text="MongoDB server hostname or IP",
            tooltip="Docker: Use container name (same network) or host.docker.internal"
        ),
        
        # Port
        FormField(
            id="port",
            label="Port",
            type="number",
            required=True,
            default=27017,
            min=1,
            max=65535,
            help_text="MongoDB server port (default: 27017)",
            tooltip="Docker: Use exposed host port (e.g., 27019) for cross-network access"
        ),
        
        # Username
        FormField(
            id="username",
            label="Username (optional)",
            type="text",
            required=False,
            placeholder="admin",
            help_text="Leave empty for no authentication"
        ),
        
        # Password
        FormField(
            id="password",
            label="Password (optional)",
            type="password",
            required=False,
            placeholder="••••••••",
            help_text="Required if username is provided"
        ),
        
        # Auth Source
        FormField(
            id="auth_source",
            label="Authentication Database",
            type="text",
            required=False,
            default="admin",
            placeholder="admin",
            help_text="Database where user credentials are stored",
            tooltip="Usually 'admin' - database where the user was created"
        ),
        
        # Database
        FormField(
            id="database",
            label="Database (optional)",
            type="text",
            required=False,
            placeholder="mydb",
            help_text="Default database to connect to"
        ),
        
        # Description
        FormField(
            id="description",
            label="Description (optional)",
            type="text",
            required=False,
            placeholder="Production database"
        )
    ],
    actions=[
        FormAction(label="Update Connection", style="primary", action="submit"),
        FormAction(label="Cancel", style="secondary", action="cancel")
    ]
)


# === BACKUP MANAGEMENT FORMS ===

# Backup Folder Add - Step 1: Configure Folder
BACKUP_FOLDER_ADD_CONFIGURE_FORM = FormSchema(
    title="Configure Folder",
    description="Enter backup folder path and options",
    step=1,
    total_steps=2,
    fields=[
        FormField(
            id="folder_path",
            label="Backup Folder Path",
            type="text",
            required=True,
            placeholder="connection-name",
            help_text="Name for this backup folder. Will be created as 'mongodb-manager-backups/your-name_mongodb_manager' automatically."
        ),
        FormField(
            id="create_if_missing",
            label="Create folder if it doesn't exist",
            type="checkbox",
            default=True,
            help_text="Automatically create the folder if not found"
        ),
        FormField(
            id="set_as_active",
            label="Set as active backup folder",
            type="checkbox",
            default=True,
            help_text="Use this folder as the default for backups"
        )
    ],
    actions=[
        FormAction(label="Next", style="primary", action="submit"),
        FormAction(label="Cancel", style="secondary", action="cancel")
    ]
)

# Backup Folder Add - Step 2: Select Connection
BACKUP_FOLDER_ADD_SELECT_FORM = FormSchema(
    title="Select Connection",
    description="Choose which connection this backup folder will be used for",
    step=2,
    total_steps=2,
    fields=[
        FormField(
            id="connection_name",
            label="Connection",
            type="select",
            required=True,
            help_text="Select the connection to add a backup folder to",
            options=[]  # Populated dynamically
        )
    ],
    actions=[
        FormAction(label="Add Folder", style="primary", action="submit"),
        FormAction(label="Cancel", style="secondary", action="cancel")
    ]
)


# Backup Folder List Form (Display form with filter)
BACKUP_FOLDER_LIST_FORM = FormSchema(
    title="Backup Folders",
    description="View backup folders configured for connections",
    fields=[
        FormField(
            id="connection_filter",
            label="Filter by Connection",
            type="select",
            required=False,
            help_text="Show folders for a specific connection or all",
            options=[
                SelectOption(value="all", label="All Connections")
            ]  # Additional options populated dynamically
        ),
        FormField(
            id="folders_list",
            label="",
            type="list",
            items=[],  # Populated dynamically with folder data
            list_config=ListDisplayConfig(
                header_icon="📁",
                fields=[
                    ListItemField(key="connection_name", label="Connection", primary=True),
                    ListItemField(key="description", label="Description", icon="📝", type="text"),
                    ListItemField(key="backup_paths", label="Backup Paths", icon="📂", type="list", badge_key="active_backup_path")
                ],
                count_label="connection(s)"
            )
        )
    ],
    actions=[
        FormAction(label="Close", style="secondary", action="cancel")
    ]
)


# Backup Create - Step 1: Select Connection
BACKUP_CREATE_SELECT_FORM = FormSchema(
    title="Select Connection",
    description="Choose connection to backup",
    step=1,
    total_steps=2,
    fields=[
        FormField(
            id="connection_name",
            label="Connection",
            type="select",
            required=True,
            help_text="Select connection (must have an active backup folder)",
            options=[]  # Populated with connections that have active_backup_path
        )
    ],
    actions=[
        FormAction(label="Next", style="primary", action="submit"),
        FormAction(label="Cancel", style="secondary", action="cancel")
    ]
)

# Backup Create - Step 2: Configure Backup
BACKUP_CREATE_CONFIGURE_FORM = FormSchema(
    title="Configure Backup",
    description="Enter backup details",
    step=2,
    total_steps=2,
    fields=[
        FormField(
            id="backup_name",
            label="Backup Name",
            type="text",
            required=True,
            placeholder="backup-2024-01-15",
            validation=ValidationRule(
                pattern=r"^[a-zA-Z0-9_-]+$",
                message="Only letters, numbers, - and _ allowed"
            ),
            help_text="Unique name for this backup (must be unique in backup folder)"
        ),
        FormField(
            id="backup_location",
            label="Backup Location",
            type="select",
            required=True,
            options=[],  # Populated dynamically with backup_paths from selected connection
            help_text="Choose the folder where backup will be saved"
        )
    ],
    actions=[
        FormAction(label="Create Backup", style="primary", action="submit"),
        FormAction(label="Cancel", style="secondary", action="cancel")
    ]
)


# Backup List Form (Display form with filter)
BACKUP_LIST_FORM = FormSchema(
    title="Backups",
    description="View all MongoDB backups",
    fields=[
        FormField(
            id="connection_filter",
            label="Filter by Connection",
            type="select",
            required=False,
            help_text="Show backups for a specific connection or all",
            options=[
                SelectOption(value="all", label="All Backups")
            ]  # Additional options populated dynamically
        ),
        FormField(
            id="backups_list",
            label="",
            type="list",
            items=[],  # Populated dynamically with backup data
            list_config=ListDisplayConfig(
                header_icon="💾",
                fields=[
                    ListItemField(key="backup_name", label="Backup Name", primary=True, icon="📦"),
                    ListItemField(key="connection_name", label="Connection", icon="🔗"),
                    ListItemField(key="folder_path", label="Location", icon="📂"),
                    ListItemField(key="created_at", label="Created", type="date", icon="📅"),
                    ListItemField(key="size", label="Size", icon="💾"),
                    ListItemField(key="databases", label="Databases", type="list", icon="🗄️")
                ],
                count_label="backup(s)"
            )
        )
    ],
    actions=[
        FormAction(label="Close", style="secondary", action="cancel")
    ]
)


# Backup Delete Form (Confirmation form)
BACKUP_DELETE_FORM = FormSchema(
    title="Delete Backup",
    description="Permanently delete a backup",
    fields=[
        FormField(
            id="backup_selector",
            label="Select Backup to Delete",
            type="select",
            required=True,
            help_text="Choose the backup to delete (this cannot be undone)",
            options=[]  # Populated with format: "folder_path|backup_name"
        ),
        FormField(
            id="warning",
            label="",
            type="readonly",
            content="⚠️ WARNING: This action cannot be undone. The backup will be permanently deleted from disk.",
            help_text=""
        ),
        FormField(
            id="confirmation",
            label="I understand this backup will be permanently deleted",
            type="checkbox",
            required=True,
            help_text="You must confirm to proceed with deletion"
        )
    ],
    actions=[
        FormAction(label="Delete Backup", style="danger", action="submit"),
        FormAction(label="Cancel", style="secondary", action="cancel")
    ]
)


# Backup Restore Forms (Multi-step)

# Step 1: Select Backup to Restore
BACKUP_RESTORE_SELECT_FORM = FormSchema(
    title="Select Backup",
    description="Select backup to restore",
    step=1,
    total_steps=2,
    fields=[
        FormField(
            id="backup_selector",
            label="Select Backup to Restore",
            type="select",
            required=True,
            help_text="Choose the backup to restore",
            options=[]  # Populated with format: "folder_path|backup_name"
        )
    ],
    actions=[
        FormAction(label="Next", style="primary", action="next"),
        FormAction(label="Cancel", style="secondary", action="cancel")
    ]
)

# Step 2: Select Connection and Configure Restore Options
BACKUP_RESTORE_CONFIGURE_FORM = FormSchema(
    title="Configure Restore",
    description="Select connection and confirm restore",
    step=2,
    total_steps=2,
    fields=[
        FormField(
            id="connection_name",
            label="Restore to Connection",
            type="select",
            required=True,
            help_text="Target connection for restore",
            options=[]  # Populated with connections
        ),
        FormField(
            id="drop_collections",
            label="Drop existing collections before restore",
            type="checkbox",
            required=False,
            default=True,
            help_text="If checked, existing collections will be dropped before restore (recommended). If unchecked, backup data will be merged with existing data."
        ),
        FormField(
            id="confirmation",
            label="I understand this will modify data in the selected connection",
            type="checkbox",
            required=True,
            help_text="Please confirm you want to proceed with the restore operation"
        )
    ],
    actions=[
        FormAction(label="Restore Backup", style="primary", action="submit"),
        FormAction(label="Cancel", style="secondary", action="cancel")
    ]
)
