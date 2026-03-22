"""Backup operation form instances"""

from app.core.forms.models import (
    FormSchema, FormField, FormAction, ValidationRule,
    SelectOption, ListDisplayConfig, ListItemField
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
            help_text="Select connection (must have at least one backup folder)",
            options=[]  # Populated with connections that have backup_paths
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
