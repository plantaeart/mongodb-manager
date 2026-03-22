"""Numeric and string constants that replace magic values throughout the codebase

Using IntEnum / StrEnum so values remain usable wherever int/str literals were.
"""

from enum import IntEnum, StrEnum


class MongoDefault(IntEnum):
    """Default numeric values for MongoDB connections"""

    PORT = 27017
    SERVER_TIMEOUT_MS = 5000


class MongoTool(StrEnum):
    """Executable names and MongoDB command strings"""

    MONGODUMP = "mongodump"
    MONGORESTORE = "mongorestore"
    PING = "ping"
    AUTH_SOURCE = "admin"


class SessionConfig(IntEnum):
    """CLI session configuration"""

    DURATION_HOURS = 24


class JwtConfig(IntEnum):
    """JWT token configuration"""

    EXPIRE_HOURS = 24
