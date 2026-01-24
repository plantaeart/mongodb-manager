"""
MongoDB Discovery Configuration Management

This module handles configuration for MongoDB instance discovery,
including network scanning parameters and connection defaults.
"""

import json
import ipaddress
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ScanSettings(BaseModel):
    """Network scanning configuration"""
    
    port_range: dict[str, int] = Field(
        default={"start": 27017, "end": 27030},
        description="Port range to scan on localhost"
    )
    timeout_seconds: int = Field(
        default=2,
        ge=1,
        le=30,
        description="Timeout in seconds for each connection probe"
    )
    max_concurrent_scans: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of concurrent scan operations"
    )
    scan_docker_networks: bool = Field(
        default=True,
        description="Enable scanning of Docker bridge networks"
    )
    docker_network_ranges: list[str] = Field(
        default=[
            "172.17.0.0/24",
            "172.18.0.0/24",
            "172.19.0.0/24",
            "172.20.0.0/24",
            "172.21.0.0/24",
            "172.22.0.0/24"
        ],
        description="Docker network CIDR ranges to scan"
    )
    custom_ip_ranges: list[str] = Field(
        default=[],
        description="Custom IP ranges in CIDR notation"
    )
    
    @field_validator("port_range")
    @classmethod
    def validate_port_range(cls, v: dict[str, int]) -> dict[str, int]:
        """Validate port range values"""
        if "start" not in v or "end" not in v:
            raise ValueError("port_range must contain 'start' and 'end' keys")
        
        start, end = v["start"], v["end"]
        
        if not (1 <= start <= 65535):
            raise ValueError(f"port_range.start must be between 1-65535, got {start}")
        if not (1 <= end <= 65535):
            raise ValueError(f"port_range.end must be between 1-65535, got {end}")
        if start >= end:
            raise ValueError(f"port_range.start ({start}) must be less than end ({end})")
        
        return v
    
    @field_validator("docker_network_ranges", "custom_ip_ranges")
    @classmethod
    def validate_ip_ranges(cls, v: list[str]) -> list[str]:
        """Validate CIDR notation for IP ranges"""
        for ip_range in v:
            try:
                ipaddress.ip_network(ip_range, strict=False)
            except ValueError as e:
                raise ValueError(f"Invalid CIDR notation '{ip_range}': {e}")
        return v


class ConnectionDefaults(BaseModel):
    """Default connection settings"""
    
    auth_source: str = Field(
        default="admin",
        description="Default authentication database"
    )
    ssl_enabled: bool = Field(
        default=False,
        description="Enable SSL/TLS by default"
    )
    direct_connection: bool = Field(
        default=False,
        description="Use direct connection mode by default"
    )


class DiscoverySettings(BaseModel):
    """Complete discovery configuration"""
    
    version: str = Field(default="1.0", description="Configuration version")
    scan_settings: ScanSettings = Field(default_factory=ScanSettings)
    connection_defaults: ConnectionDefaults = Field(default_factory=ConnectionDefaults)
    
    @classmethod
    def get_config_path(cls) -> Path:
        """Returns path to discovery_config.json"""
        return Path(__file__).parent / "discovery_config.json"
    
    @classmethod
    def load(cls) -> "DiscoverySettings":
        """
        Load settings from config file
        
        If file doesn't exist or is invalid, returns default settings
        and creates the config file.
        """
        config_path = cls.get_config_path()
        
        try:
            if config_path.exists():
                with open(config_path, "r") as f:
                    data = json.load(f)
                    settings = cls(**data)
                    return settings
        except (json.JSONDecodeError, ValueError) as e:
            # Config file is corrupted, will create new one
            print(f"Warning: Config file corrupted ({e}), using defaults")
        
        # Create default config
        settings = cls()
        settings.save()
        return settings
    
    def save(self) -> None:
        """Save current settings to config file"""
        config_path = self.get_config_path()
        
        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write config with pretty formatting
        with open(config_path, "w") as f:
            json.dump(
                self.model_dump(),
                f,
                indent=2,
                ensure_ascii=False
            )
    
    def reset_to_defaults(self) -> "DiscoverySettings":
        """
        Reset all settings to factory defaults
        
        Returns new DiscoverySettings instance with defaults
        """
        default_settings = DiscoverySettings()
        default_settings.save()
        return default_settings
    
    def update_port_range(self, start: int, end: int) -> None:
        """
        Update port range with validation
        
        Args:
            start: Starting port number (1-65535)
            end: Ending port number (1-65535)
        
        Raises:
            ValueError: If ports are invalid or start >= end
        """
        if not (1 <= start <= 65535):
            raise ValueError(f"Start port must be between 1-65535, got {start}")
        if not (1 <= end <= 65535):
            raise ValueError(f"End port must be between 1-65535, got {end}")
        if start >= end:
            raise ValueError(f"Start port ({start}) must be less than end ({end})")
        
        self.scan_settings.port_range = {"start": start, "end": end}
    
    def update_timeout(self, seconds: int) -> None:
        """
        Update timeout with validation
        
        Args:
            seconds: Timeout in seconds (1-30)
        
        Raises:
            ValueError: If timeout is out of range
        """
        if not (1 <= seconds <= 30):
            raise ValueError(f"Timeout must be between 1-30 seconds, got {seconds}")
        
        self.scan_settings.timeout_seconds = seconds
    
    def update_max_concurrent(self, count: int) -> None:
        """
        Update max concurrent scans with validation
        
        Args:
            count: Maximum concurrent scans (1-50)
        
        Raises:
            ValueError: If count is out of range
        """
        if not (1 <= count <= 50):
            raise ValueError(f"Max concurrent must be between 1-50, got {count}")
        
        self.scan_settings.max_concurrent_scans = count
    
    def toggle_docker_scan(self, enabled: bool) -> None:
        """
        Enable or disable Docker network scanning
        
        Args:
            enabled: True to enable, False to disable
        """
        self.scan_settings.scan_docker_networks = enabled
    
    def add_ip_range(self, ip_range: str) -> None:
        """
        Add custom IP range with CIDR validation
        
        Args:
            ip_range: IP range in CIDR notation (e.g., "192.168.1.0/24")
        
        Raises:
            ValueError: If CIDR notation is invalid or range already exists
        """
        # Validate CIDR notation
        try:
            ipaddress.ip_network(ip_range, strict=False)
        except ValueError as e:
            raise ValueError(f"Invalid CIDR notation '{ip_range}': {e}")
        
        # Check if already exists
        if ip_range in self.scan_settings.custom_ip_ranges:
            raise ValueError(f"IP range '{ip_range}' already exists")
        
        self.scan_settings.custom_ip_ranges.append(ip_range)
    
    def remove_ip_range(self, ip_range: str) -> None:
        """
        Remove custom IP range
        
        Args:
            ip_range: IP range to remove
        
        Raises:
            ValueError: If range doesn't exist
        """
        if ip_range not in self.scan_settings.custom_ip_ranges:
            raise ValueError(f"IP range '{ip_range}' not found in custom ranges")
        
        self.scan_settings.custom_ip_ranges.remove(ip_range)
    
    def add_docker_range(self, ip_range: str) -> None:
        """
        Add Docker network range with CIDR validation
        
        Args:
            ip_range: IP range in CIDR notation (e.g., "172.23.0.0/24")
        
        Raises:
            ValueError: If CIDR notation is invalid or range already exists
        """
        # Validate CIDR notation
        try:
            ipaddress.ip_network(ip_range, strict=False)
        except ValueError as e:
            raise ValueError(f"Invalid CIDR notation '{ip_range}': {e}")
        
        # Check if already exists
        if ip_range in self.scan_settings.docker_network_ranges:
            raise ValueError(f"Docker network range '{ip_range}' already exists")
        
        self.scan_settings.docker_network_ranges.append(ip_range)
    
    def remove_docker_range(self, ip_range: str) -> None:
        """
        Remove Docker network range
        
        Args:
            ip_range: IP range to remove
        
        Raises:
            ValueError: If range doesn't exist
        """
        if ip_range not in self.scan_settings.docker_network_ranges:
            raise ValueError(f"Docker network range '{ip_range}' not found")
        
        self.scan_settings.docker_network_ranges.remove(ip_range)
    
    def get_all_ip_ranges(self) -> list[str]:
        """
        Get combined Docker + custom IP ranges
        
        Returns:
            List of all IP ranges that should be scanned
        """
        ranges = []
        
        if self.scan_settings.scan_docker_networks:
            ranges.extend(self.scan_settings.docker_network_ranges)
        
        ranges.extend(self.scan_settings.custom_ip_ranges)
        
        return ranges
    
    def validate_ip_range(self, ip_range: str) -> bool:
        """
        Validate CIDR notation
        
        Args:
            ip_range: IP range to validate
        
        Returns:
            True if valid, False otherwise
        """
        try:
            ipaddress.ip_network(ip_range, strict=False)
            return True
        except ValueError:
            return False
    
    def to_display_dict(self) -> dict[str, Any]:
        """
        Return formatted dict for display in Rich table
        
        Returns:
            Dictionary with formatted values for display
        """
        port_range = self.scan_settings.port_range
        
        return {
            "Port Range": f"{port_range['start']} - {port_range['end']}",
            "Scan Timeout": f"{self.scan_settings.timeout_seconds} seconds",
            "Max Concurrent Scans": str(self.scan_settings.max_concurrent_scans),
            "Docker Network Scanning": "Enabled" if self.scan_settings.scan_docker_networks else "Disabled",
            "Docker Network Ranges": self.scan_settings.docker_network_ranges,
            "Custom IP Ranges": self.scan_settings.custom_ip_ranges if self.scan_settings.custom_ip_ranges else ["None configured"],
            "Auth Source (default)": self.connection_defaults.auth_source,
            "SSL Enabled (default)": "Yes" if self.connection_defaults.ssl_enabled else "No",
            "Direct Connection (default)": "Yes" if self.connection_defaults.direct_connection else "No",
        }
