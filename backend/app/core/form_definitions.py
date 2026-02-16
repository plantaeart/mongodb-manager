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


class FormField(BaseModel):
    """Form field definition"""
    id: str
    label: str
    type: Literal['text', 'textarea', 'number', 'select', 'checkbox', 'date', 'readonly', 'password']
    required: bool = False
    placeholder: Optional[str] = None
    default: Any = None
    validation: Optional[ValidationRule] = None
    help_text: Optional[str] = None
    
    # Type-specific fields
    rows: Optional[int] = None  # textarea
    min: Optional[int | float] = None  # number, date
    max: Optional[int | float] = None  # number, date
    step: Optional[int | float] = None  # number
    options: Optional[List[SelectOption]] = None  # select
    content: Optional[str] = None  # readonly


class FormAction(BaseModel):
    """Form action button"""
    label: str
    style: Literal['primary', 'secondary', 'danger']
    action: str


class FormSchema(BaseModel):
    """Single-step form schema"""
    title: str
    description: Optional[str] = None
    fields: List[FormField]
    actions: List[FormAction]


class FormStep(BaseModel):
    """Step in multi-step form"""
    id: str
    title: str
    description: Optional[str] = None
    fields: List[FormField]


class FormStepperSchema(BaseModel):
    """Multi-step form schema"""
    title: str
    description: Optional[str] = None
    steps: List[FormStep]
    actions: Dict[str, FormAction]  # next, previous, submit, cancel


# === FORM DEFINITIONS ===

# Connection Add Form (Hybrid: Simple & Advanced modes)
CONNECT_ADD_FORM = FormSchema(
    title="Add MongoDB Connection",
    description="Enter connection details",
    fields=[
        # ALWAYS VISIBLE: Connection Name
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
        
        # SIMPLE MODE ONLY: MongoDB URI
        FormField(
            id="uri",
            label="MongoDB URI",
            type="text",
            required=True,
            default="mongodb://localhost:27017",
            placeholder="mongodb://host:port",
            validation=ValidationRule(
                pattern=r"^mongodb://.*",
                message="Must start with mongodb://"
            ),
            help_text="Format: mongodb://[username:password@]host:port[/database]"
        ),
        
        # ADVANCED MODE ONLY: Host
        FormField(
            id="host",
            label="Host",
            type="text",
            required=False,
            default="localhost",
            placeholder="localhost or IP address",
            help_text="MongoDB server hostname or IP"
        ),
        
        # ADVANCED MODE ONLY: Port
        FormField(
            id="port",
            label="Port",
            type="number",
            required=False,
            default=27017,
            min=1,
            max=65535,
            help_text="MongoDB server port (default: 27017)"
        ),
        
        # ADVANCED MODE ONLY: Username
        FormField(
            id="username",
            label="Username (optional)",
            type="text",
            required=False,
            placeholder="admin",
            help_text="Leave empty for no authentication"
        ),
        
        # ADVANCED MODE ONLY: Password
        FormField(
            id="password",
            label="Password (optional)",
            type="password",
            required=False,
            placeholder="••••••••",
            help_text="Required if username is provided"
        ),
        
        # ADVANCED MODE ONLY: Auth Source
        FormField(
            id="auth_source",
            label="Authentication Database",
            type="text",
            required=False,
            default="admin",
            placeholder="admin",
            help_text="Database where user credentials are stored"
        ),
        
        # ADVANCED MODE ONLY: Database
        FormField(
            id="database",
            label="Database (optional)",
            type="text",
            required=False,
            placeholder="mydb",
            help_text="Default database to connect to"
        ),
        
        # ALWAYS VISIBLE: Description
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
