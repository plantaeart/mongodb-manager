"""MongoDB URI builder utility

Constructs MongoDB connection URIs from components with proper encoding.
"""

from urllib.parse import quote_plus


def build_mongodb_uri(
    host: str,
    port: int = 27017,
    username: str | None = None,
    password: str | None = None,
    database: str | None = None,
    auth_source: str | None = None,
    options: dict | None = None
) -> str:
    """
    Construct MongoDB URI from components
    
    Args:
        host: MongoDB server hostname or IP address
        port: MongoDB server port (default: 27017)
        username: Optional username for authentication
        password: Optional password for authentication
        database: Optional default database
        auth_source: Authentication database (default: "admin")
        options: Optional connection options dict
        
    Returns:
        Complete MongoDB connection URI
        
    Examples:
        >>> build_mongodb_uri("localhost", 27017)
        'mongodb://localhost:27017'
        
        >>> build_mongodb_uri("localhost", 27017, "admin", "pass123")
        'mongodb://admin:pass123@localhost:27017?authSource=admin'
        
        >>> build_mongodb_uri("db.example.com", 27017, "user@email", "p@ss:w0rd")
        'mongodb://user%40email:p%40ss%3Aw0rd@db.example.com:27017?authSource=admin'
        
    Raises:
        ValueError: If required fields are invalid
    """
    # Validate inputs
    if not host or not host.strip():
        raise ValueError("Host cannot be empty")
    
    if not isinstance(port, int) or port < 1 or port > 65535:
        raise ValueError(f"Port must be between 1 and 65535, got: {port}")
    
    # Both username and password must be provided together
    if (username and not password) or (password and not username):
        raise ValueError("Both username and password must be provided together")
    
    # Build URI components
    uri_parts = ["mongodb://"]
    
    # Add credentials if provided
    if username and password:
        # URL-encode username and password to handle special characters
        encoded_username = quote_plus(username)
        encoded_password = quote_plus(password)
        uri_parts.append(f"{encoded_username}:{encoded_password}@")
    
    # Add host and port
    uri_parts.append(f"{host}:{port}")
    
    # Add database if provided
    if database and database.strip():
        uri_parts.append(f"/{database}")
    
    # Build query parameters
    query_params = []
    
    # Add authSource if credentials provided
    if username and password and auth_source:
        query_params.append(f"authSource={auth_source}")
    
    # Add custom options
    if options:
        for key, value in options.items():
            query_params.append(f"{key}={value}")
    
    # Append query string if there are parameters
    if query_params:
        uri_parts.append("?" + "&".join(query_params))
    
    return "".join(uri_parts)


def build_mongodb_uri_masked(
    host: str,
    port: int = 27017,
    username: str | None = None,
    database: str | None = None,
    auth_source: str | None = None,
    options: dict | None = None
) -> str:
    """
    Build MongoDB URI from components with masked password for display
    
    Args:
        host: MongoDB server hostname or IP address
        port: MongoDB server port (default: 27017)
        username: Optional username for authentication (password will be ***)
        database: Optional default database
        auth_source: Authentication database (default: "admin")
        options: Optional connection options dict
        
    Returns:
        MongoDB URI with password masked as ***
        
    Examples:
        >>> build_mongodb_uri_masked("localhost", 27017, "admin")
        'mongodb://admin:***@localhost:27017?authSource=admin'
        
        >>> build_mongodb_uri_masked("localhost", 27017)
        'mongodb://localhost:27017'
    """
    # Build URI components
    uri_parts = ["mongodb://"]
    
    # Add credentials if username provided (password is always ***)
    if username:
        uri_parts.append(f"{username}:***@")
    
    # Add host and port
    uri_parts.append(f"{host}:{port}")
    
    # Add database if provided
    if database and database.strip():
        uri_parts.append(f"/{database}")
    
    # Build query parameters
    query_params = []
    
    # Add authSource if credentials provided
    if username and auth_source:
        query_params.append(f"authSource={auth_source}")
    
    # Add custom options
    if options:
        for key, value in options.items():
            query_params.append(f"{key}={value}")
    
    # Append query string if there are parameters
    if query_params:
        uri_parts.append("?" + "&".join(query_params))
    
    return "".join(uri_parts)
