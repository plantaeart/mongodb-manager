"""Command and form-path string enums

Replaces raw magic strings used in if-chain dispatching across
routers/commands.py and routers/forms.py.
"""

from enum import StrEnum


class Command(StrEnum):
    """CLI command strings received from the frontend"""

    CONNECT_ADD = "connect add"
    CONNECT_REMOVE = "connect remove"
    CONNECT_TEST = "connect test"
    CONNECT_UPDATE = "connect update"
    BACKUP_FOLDER_ADD = "backup folder add"
    BACKUP_FOLDER_DELETE = "backup folder delete"
    BACKUP_CREATE = "backup create"
    BACKUP_RESTORE = "backup restore"


class FormPath(StrEnum):
    """Form-schema path strings used as keys in the FORM_REGISTRY"""

    CONNECT_ADD = "connect/add"
    CONNECT_REMOVE = "connect/remove"
    CONNECT_LIST = "connect/list"
    CONNECT_TEST = "connect/test"
    CONNECT_UPDATE_SELECT = "connect/update/select"
    CONNECT_UPDATE_DETAILS = "connect/update/details"

    BACKUP_FOLDER_ADD_SELECT = "backup/folder/add/select"
    BACKUP_FOLDER_ADD_CONFIGURE = "backup/folder/add/configure"
    BACKUP_FOLDER_DELETE_SELECT = "backup/folder/delete/select"
    BACKUP_FOLDER_DELETE_CONFIRM = "backup/folder/delete/confirm"
    BACKUP_FOLDER_LIST = "backup/folder/list"

    BACKUP_CREATE_SELECT = "backup/create/select"
    BACKUP_CREATE_CONFIGURE = "backup/create/configure"
    BACKUP_LIST = "backup/list"
    BACKUP_DELETE = "backup/delete"
    BACKUP_RESTORE_SELECT = "backup/restore/select"
    BACKUP_RESTORE_CONFIGURE = "backup/restore/configure"
