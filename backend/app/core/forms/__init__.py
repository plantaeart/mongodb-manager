"""Form definitions package — re-exports all models and form instances for backward compatibility"""

from app.core.forms.models import (
    ValidationRule,
    SelectOption,
    ListItemField,
    ListDisplayConfig,
    FormField,
    FormAction,
    FormSchema,
)

from app.core.forms.connect import (
    CONNECT_ADD_FORM,
    CONNECT_REMOVE_FORM,
    CONNECT_LIST_FORM,
    CONNECT_TEST_FORM,
    CONNECT_UPDATE_SELECT_FORM,
    CONNECT_UPDATE_DETAILS_FORM,
)

from app.core.forms.backup_folder import (
    BACKUP_FOLDER_ADD_CONFIGURE_FORM,
    BACKUP_FOLDER_ADD_SELECT_FORM,
    BACKUP_FOLDER_DELETE_SELECT_FORM,
    BACKUP_FOLDER_DELETE_CONFIRM_FORM,
    BACKUP_FOLDER_LIST_FORM,
)

from app.core.forms.backup_ops import (
    BACKUP_CREATE_SELECT_FORM,
    BACKUP_CREATE_CONFIGURE_FORM,
    BACKUP_LIST_FORM,
    BACKUP_DELETE_FORM,
    BACKUP_RESTORE_SELECT_FORM,
    BACKUP_RESTORE_CONFIGURE_FORM,
)

__all__ = [
    # Models
    "ValidationRule",
    "SelectOption",
    "ListItemField",
    "ListDisplayConfig",
    "FormField",
    "FormAction",
    "FormSchema",
    # Connection forms
    "CONNECT_ADD_FORM",
    "CONNECT_REMOVE_FORM",
    "CONNECT_LIST_FORM",
    "CONNECT_TEST_FORM",
    "CONNECT_UPDATE_SELECT_FORM",
    "CONNECT_UPDATE_DETAILS_FORM",
    # Backup folder forms
    "BACKUP_FOLDER_ADD_CONFIGURE_FORM",
    "BACKUP_FOLDER_ADD_SELECT_FORM",
    "BACKUP_FOLDER_DELETE_SELECT_FORM",
    "BACKUP_FOLDER_DELETE_CONFIRM_FORM",
    "BACKUP_FOLDER_LIST_FORM",
    # Backup operation forms
    "BACKUP_CREATE_SELECT_FORM",
    "BACKUP_CREATE_CONFIGURE_FORM",
    "BACKUP_LIST_FORM",
    "BACKUP_DELETE_FORM",
    "BACKUP_RESTORE_SELECT_FORM",
    "BACKUP_RESTORE_CONFIGURE_FORM",
]
