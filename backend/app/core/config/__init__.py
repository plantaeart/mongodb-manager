"""
Configuration module for MongoDB discovery
"""

from .discovery_settings import (
    DiscoverySettings,
    ScanSettings,
    ConnectionDefaults,
)

__all__ = [
    "DiscoverySettings",
    "ScanSettings",
    "ConnectionDefaults",
]
