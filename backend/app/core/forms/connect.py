"""Connection form instances"""

from app.core.forms.models import (
    FormSchema, FormField, FormAction, ValidationRule,
    ListDisplayConfig, ListItemField, SelectOption
)

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
            tooltip="Usually 'admin' - leave empty if no authentication is used"
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
            tooltip="Usually 'admin' - leave empty if no authentication is used"
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
