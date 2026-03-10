"""
Docker Service for Container Discovery

Provides read-only access to Docker API for discovering container names
and mapping IP addresses to container identities.
"""

import logging
from typing import Optional
import docker
from docker.errors import DockerException

logger = logging.getLogger(__name__)


class DockerService:
    """Service for interacting with Docker API (read-only)"""
    
    def __init__(self):
        """Initialize Docker client with error handling"""
        self.client: Optional[docker.DockerClient] = None
        self.available = False
        
        try:
            # Try to connect to Docker socket
            self.client = docker.from_env()
            # Test connection
            self.client.ping()
            self.available = True
        except DockerException as e:
            pass
        except Exception as e:
            pass
    
    def get_container_name_by_ip(self, ip_address: str) -> Optional[str]:
        """
        Look up container name by IP address
        
        Args:
            ip_address: IP address to lookup (e.g., "172.21.0.2")
        
        Returns:
            Container name if found, None otherwise
        """
        if not self.available or not self.client:
            return None
        
        try:
            # Get all containers
            containers = self.client.containers.list()
            
            for container in containers:
                # Check all network settings
                networks = container.attrs.get('NetworkSettings', {}).get('Networks', {})
                
                for network_name, network_info in networks.items():
                    container_ip = network_info.get('IPAddress', '')
                    
                    if container_ip == ip_address:
                        # Return container name (remove leading slash if present)
                        name = container.name
                        return name.lstrip('/')
            
            return None
            
        except Exception as e:
            return None
    
    def get_container_info_by_ip(self, ip_address: str) -> Optional[dict]:
        """
        Get detailed container information by IP address
        
        Args:
            ip_address: IP address to lookup
        
        Returns:
            Dict with container info: {name, id, image, labels, networks}
        """
        if not self.available or not self.client:
            return None
        
        try:
            containers = self.client.containers.list()
            
            for container in containers:
                networks = container.attrs.get('NetworkSettings', {}).get('Networks', {})
                
                for network_name, network_info in networks.items():
                    container_ip = network_info.get('IPAddress', '')
                    
                    if container_ip == ip_address:
                        return {
                            'name': container.name.lstrip('/'),
                            'id': container.short_id,
                            'image': container.image.tags[0] if container.image.tags else 'unknown',
                            'labels': container.labels,
                            'networks': list(networks.keys()),
                            'status': container.status
                        }
            
            return None
            
        except Exception as e:
            return None
    
    def is_available(self) -> bool:
        """Check if Docker API is available"""
        return self.available
    
    def close(self):
        """Close Docker client connection"""
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass


# Global singleton instance
_docker_service: Optional[DockerService] = None


def get_docker_service() -> DockerService:
    """
    Get or create the global DockerService instance
    
    Returns:
        DockerService singleton
    """
    global _docker_service
    if _docker_service is None:
        _docker_service = DockerService()
    return _docker_service
