"""
Network Scanner for MongoDB Discovery

Scans networks for MongoDB instances with optional Docker container name lookup.
Uses TCP probing and MongoDB protocol detection.
"""

import socket
import ipaddress
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure, ServerSelectionTimeoutError

from ..models.mongodb_instance import MongoDBInstance
from .config import DiscoverySettings
from .docker_service import get_docker_service


# Configure logging
logger = logging.getLogger(__name__)


class NetworkScanner:
    """
    Network scanner for discovering MongoDB instances
    
    Scans using:
    - TCP port scanning
    - MongoDB protocol detection
    - Docker container name lookup (if available)
    - Parallel execution for performance
    """
    
    def __init__(self, settings: DiscoverySettings | None = None):
        """
        Initialize scanner with settings
        
        Args:
            settings: DiscoverySettings instance (loads defaults if None)
        """
        self.settings = settings or DiscoverySettings.load()
        self.timeout = self.settings.scan_settings.timeout_seconds
        self.max_workers = self.settings.scan_settings.max_concurrent_scans
        self.docker_service = get_docker_service()
    
    def scan_all(self, progress_callback: Callable[[str], None] | None = None) -> list[MongoDBInstance]:
        """
        Scan all configured sources for MongoDB instances
        
        Args:
            progress_callback: Optional callback function to report progress
        
        Returns:
            List of discovered MongoDBInstance objects
        """
        all_instances = []
        
        # Scan localhost ports
        if progress_callback:
            progress_callback("Scanning localhost ports...")
        
        localhost_instances = self.scan_localhost_ports()
        all_instances.extend(localhost_instances)
        
        if progress_callback:
            progress_callback(f"Found {len(localhost_instances)} instance(s) on localhost")
        
        # Scan IP ranges
        ip_ranges = self.settings.get_all_ip_ranges()
        
        if ip_ranges:
            if progress_callback:
                progress_callback(f"Scanning {len(ip_ranges)} network range(s)...")
            
            for ip_range in ip_ranges:
                network_instances = self.scan_ip_range(ip_range)
                all_instances.extend(network_instances)
            
            if progress_callback:
                progress_callback(f"Found {len(all_instances) - len(localhost_instances)} instance(s) on networks")
        
        return all_instances
    
    def scan_localhost_ports(self) -> list[MongoDBInstance]:
        """
        Scan localhost for MongoDB on configured port range
        
        Uses parallel scanning with max_concurrent_scans limit
        
        Returns:
            List of discovered MongoDBInstance objects
        """
        port_range = self.settings.scan_settings.port_range
        start_port = port_range["start"]
        end_port = port_range["end"]
        
        instances = []
        hosts = ["localhost", "127.0.0.1"]
        
        # Create list of (host, port) tuples to scan
        scan_targets = []
        for host in hosts:
            for port in range(start_port, end_port + 1):
                scan_targets.append((host, port))
        
        # Scan in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all probe tasks
            future_to_target = {
                executor.submit(self.probe_mongodb, host, port): (host, port)
                for host, port in scan_targets
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_target):
                instance = future.result()
                if instance and instance.detected:
                    # Avoid duplicates (localhost and 127.0.0.1 are the same)
                    if not any(
                        i.port == instance.port and i.get_location_type() == "localhost"
                        for i in instances
                    ):
                        instances.append(instance)
        
        return instances
    
    def scan_ip_range(self, ip_range: str) -> list[MongoDBInstance]:
        """
        Scan IP range (CIDR notation) for MongoDB on standard port
        
        Smart scanning:
        - Only scans gateway IPs (.2-.10) in /24 networks
        - Full scan for smaller networks
        - Respects timeout and concurrency settings
        
        Args:
            ip_range: IP range in CIDR notation (e.g., "172.17.0.0/24")
        
        Returns:
            List of discovered MongoDBInstance objects
        """
        try:
            network = ipaddress.ip_network(ip_range, strict=False)
        except ValueError as e:
            logger.error(f"Invalid IP range '{ip_range}': {e}")
            return []
        
        # Get IPs to scan
        ips_to_scan = self._get_gateway_ips(ip_range)
        
        # Use standard MongoDB port for network scanning
        standard_port = 27017
        
        instances = []
        
        # Scan in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all probe tasks
            future_to_ip = {
                executor.submit(self.probe_mongodb, str(ip), standard_port): ip
                for ip in ips_to_scan
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_ip):
                instance = future.result()
                if instance and instance.detected:
                    instances.append(instance)
        
        return instances
    
    def probe_mongodb(self, host: str, port: int) -> MongoDBInstance | None:
        """
        Probe single host:port for MongoDB
        
        Steps:
        1. TCP connection test
        2. MongoDB hello command (no auth)
        3. Extract version and server info
        4. Detect auth requirement
        
        Args:
            host: IP address or hostname
            port: Port number
        
        Returns:
            MongoDBInstance if MongoDB detected, None otherwise
        """
        # Step 1: TCP connection test
        if not self._tcp_probe(host, port):
            return None
        
        # Step 2: Try to get MongoDB server info
        server_info = self._get_server_info_no_auth(host, port)
        
        if not server_info:
            return None  # Not a MongoDB instance
        
        # Step 3: Extract version
        version = server_info.get("version", None)
        
        # Step 4: Detect auth requirement
        requires_auth = self._detect_auth_requirement(host, port)
        
        # Step 5: Look up Docker container name (if available)
        container_name = None
        if self.docker_service.is_available():
            container_name = self.docker_service.get_container_name_by_ip(host)
            if container_name:
                logger.debug(f"Found container name '{container_name}' for {host}:{port}")
        
        # Step 6: Create MongoDBInstance
        instance = MongoDBInstance(
            host=host,
            port=port,
            version=version,
            detected=True,
            requires_auth=requires_auth,
            server_info=server_info,
            container_name=container_name,
        )
        
        # Generate connection URI
        instance.connection_uri = instance.get_connection_uri()
        
        return instance
    
    def _tcp_probe(self, host: str, port: int) -> bool:
        """
        Test TCP connection with timeout
        
        Args:
            host: IP address or hostname
            port: Port number
        
        Returns:
            True if TCP connection succeeds, False otherwise
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except (socket.error, socket.timeout):
            return False
        except Exception as e:
            logger.debug(f"TCP probe error for {host}:{port}: {e}")
            return False
    
    def _get_server_info_no_auth(self, host: str, port: int) -> dict | None:
        """
        Get MongoDB server info without authentication
        
        Uses 'hello' command which works without auth
        
        Args:
            host: IP address or hostname
            port: Port number
        
        Returns:
            Server info dict or None if not MongoDB
        """
        try:
            # Build URI without credentials
            uri = f"mongodb://{host}:{port}/?directConnection=true"
            
            client = MongoClient(
                uri,
                serverSelectionTimeoutMS=self.timeout * 1000,
                connectTimeoutMS=self.timeout * 1000
            )
            
            # Try to get server info (works without auth)
            info = client.server_info()
            
            client.close()
            return info
            
        except ServerSelectionTimeoutError:
            return None  # Timeout - not reachable
        except ConnectionFailure:
            return None  # Connection failed - not MongoDB
        except Exception as e:
            logger.debug(f"Server info error for {host}:{port}: {e}")
            return None
    
    def _detect_auth_requirement(self, host: str, port: int) -> bool:
        """
        Detect if MongoDB requires authentication
        
        Tries to list databases without auth
        
        Args:
            host: IP address or hostname
            port: Port number
        
        Returns:
            True if auth required, False if no auth needed
        """
        try:
            # Build URI without credentials
            uri = f"mongodb://{host}:{port}/?directConnection=true"
            
            client = MongoClient(
                uri,
                serverSelectionTimeoutMS=self.timeout * 1000,
                connectTimeoutMS=self.timeout * 1000
            )
            
            # Try to list databases (requires auth if enabled)
            try:
                client.list_database_names()
                client.close()
                return False  # No auth required
            except OperationFailure as e:
                client.close()
                # Check if error is auth-related
                error_msg = str(e).lower()
                if "authentication" in error_msg or "unauthorized" in error_msg or "not authorized" in error_msg:
                    return True  # Auth required
                return True  # Other permission error, assume auth required
            
        except Exception as e:
            logger.debug(f"Auth detection error for {host}:{port}: {e}")
            return True  # Assume auth required on error
    
    def _get_gateway_ips(self, network_cidr: str) -> list[ipaddress.IPv4Address]:
        """
        Get likely gateway IPs from network CIDR
        
        Smart scanning strategy:
        - For /24 networks: Returns .2 through .10 (typical Docker gateway range)
        - For /16 or larger: Returns .0.2 through .0.10 from first subnet
        - For smaller networks: Returns all usable IPs
        
        Args:
            network_cidr: Network in CIDR notation (e.g., "172.17.0.0/24")
        
        Returns:
            List of IP addresses to scan
        """
        try:
            network = ipaddress.ip_network(network_cidr, strict=False)
        except ValueError:
            return []
        
        # Get all hosts in network
        hosts = list(network.hosts())
        
        if not hosts:
            return []
        
        # For /24 networks (common Docker networks), scan typical gateway IPs
        if network.prefixlen == 24:
            # Scan .2 through .10
            gateway_ips = []
            for i in range(2, 11):
                try:
                    ip = ipaddress.IPv4Address(str(network.network_address + i))
                    if ip in hosts:
                        gateway_ips.append(ip)
                except:
                    pass
            return gateway_ips if gateway_ips else hosts[:10]
        
        # For smaller networks (more hosts), return first 20 IPs
        elif network.prefixlen >= 16:
            return hosts[:20]
        
        # For larger networks, return first 50 IPs
        else:
            return hosts[:50]
