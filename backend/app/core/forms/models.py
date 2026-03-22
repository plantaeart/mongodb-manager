"""Pydantic model classes for WebSocket terminal form schemas"""

from typing import Any, Literal
from pydantic import BaseModel


class ValidationRule(BaseModel):
    """Validation rules for form fields"""
    pattern: str | None = None
    message: str = "Invalid value"
    min: int | float | None = None
    max: int | float | None = None


class SelectOption(BaseModel):
    """Option for select fields"""
    value: str
    label: str
    description: str | None = None
    metadata: dict[str, Any] | None = None


class ListItemField(BaseModel):
    """Configuration for displaying a field in a list item"""
    key: str  # The property key in the item object
    label: str  # Display label for this field
    icon: str | None = None  # Optional emoji icon
    type: Literal['text', 'date', 'list', 'badge'] | None = 'text'  # How to render the value
    primary: bool | None = False  # If true, shown in header
    badge_key: str | None = None  # For type='badge', the key to compare for active state


class ListDisplayConfig(BaseModel):
    """Configuration for how to display list items"""
    header_icon: str | None = None  # Icon for the header
    fields: list[ListItemField]  # Fields to display
    count_label: str | None = "item(s)"  # Label for total count


class FormField(BaseModel):
    """Form field definition"""
    id: str
    label: str
    type: Literal['text', 'textarea', 'number', 'select', 'checkbox', 'checkbox-list', 'date', 'readonly', 'password', 'list']
    required: bool = False
    placeholder: str | None = None
    default: Any = None
    validation: ValidationRule | None = None
    help_text: str | None = None
    tooltip: str | None = None  # Tooltip text for info icon

    # Type-specific fields
    rows: int | None = None  # textarea
    min: int | float | None = None  # number, date
    max: int | float | None = None  # number, date
    step: int | float | None = None  # number
    options: list[SelectOption] | None = None  # select, checkbox-list
    content: str | None = None  # readonly
    items: list[dict[str, Any]] | None = None  # list
    list_config: ListDisplayConfig | None = None  # Configuration for list display


class FormAction(BaseModel):
    """Form action button"""
    label: str
    style: Literal['primary', 'secondary', 'danger']
    action: str


class FormSchema(BaseModel):
    """Form schema (supports both single-step and multi-step forms)"""
    title: str
    description: str | None = None
    step: int | None = None  # Step number (1-indexed) for multi-step forms
    total_steps: int | None = None  # Total steps in multi-step flow
    fields: list[FormField]
    actions: list[FormAction]
