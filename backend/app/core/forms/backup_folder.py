"""Backup folder management form instances"""

from app.core.forms.models import (
    FormSchema, FormField, FormAction, SelectOption,
    ListDisplayConfig, ListItemField
)

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


# Backup Folder Delete - Step 1: Select Connection
# Note: Options are populated dynamically (only connections with backup folders)
BACKUP_FOLDER_DELETE_SELECT_FORM = FormSchema(
    title="Select Connection",
    description="Choose which connection's backup folder you want to delete",
    step=1,
    total_steps=2,
    fields=[
        FormField(
            id="connection_name",
            label="Connection",
            type="select",
            required=True,
            help_text="Select the connection whose backup folder you want to remove",
            options=[]  # Populated dynamically (only connections with backup_paths)
        )
    ],
    actions=[
        FormAction(label="Next", style="primary", action="submit"),
        FormAction(label="Cancel", style="secondary", action="cancel")
    ]
)

# Backup Folder Delete - Step 2: Select Folder & Confirm
# Note: Options are populated dynamically from the connection selected in step 1
BACKUP_FOLDER_DELETE_CONFIRM_FORM = FormSchema(
    title="Delete Backup Folder",
    description="Select the folder to remove and confirm",
    step=2,
    total_steps=2,
    fields=[
        FormField(
            id="folder_path",
            label="Backup Folder",
            type="select",
            required=True,
            help_text="Select the backup folder to permanently delete",
            options=[]  # Populated dynamically from selected connection's backup_paths
        ),
        FormField(
            id="warning",
            label="",
            type="readonly",
            content="⚠️ WARNING: This will permanently delete the folder and ALL backup files inside it. This action cannot be undone.",
            help_text=""
        ),
        FormField(
            id="confirmation",
            label="I understand this will permanently delete the folder and all its backups",
            type="checkbox",
            required=True,
            help_text="You must confirm to proceed with deletion"
        )
    ],
    actions=[
        FormAction(label="Delete Folder", style="danger", action="submit"),
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
                    ListItemField(key="backup_paths", label="Backup Paths", icon="📂", type="list")
                ],
                count_label="connection(s)"
            )
        )
    ],
    actions=[
        FormAction(label="Close", style="secondary", action="cancel")
    ]
)
