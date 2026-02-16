"""
Utility functions for URL validation and security
"""
from urllib.parse import urlparse


def validate_url_safety(url: str) -> None:
    """
    Validate that a URL is safe to access (no SSRF attacks).
    Raises ValueError if the URL is not safe.
    """
    parsed = urlparse(url)
    
    # Only allow http and https schemes
    if parsed.scheme not in ('http', 'https'):
        raise ValueError(f"Invalid URL scheme: {parsed.scheme}. Only http and https are allowed.")
    
    # Prevent access to localhost and private IP ranges
    hostname = parsed.hostname
    if hostname:
        hostname_lower = hostname.lower()
        
        # Check for localhost variants
        if hostname_lower in ('localhost', '127.0.0.1', '0.0.0.0', '::1'):
            raise ValueError(f"Access to private/local networks is not allowed: {hostname}")
        
        # Check for private IP ranges
        # 192.168.0.0/16
        if hostname_lower.startswith('192.168.'):
            raise ValueError(f"Access to private/local networks is not allowed: {hostname}")
        
        # 10.0.0.0/8
        if hostname_lower.startswith('10.'):
            raise ValueError(f"Access to private/local networks is not allowed: {hostname}")
        
        # 172.16.0.0/12 (172.16.0.0 - 172.31.255.255)
        if hostname_lower.startswith('172.'):
            parts = hostname_lower.split('.')
            if len(parts) >= 2 and parts[1].isdigit():
                second_octet = int(parts[1])
                if 16 <= second_octet <= 31:
                    raise ValueError(f"Access to private/local networks is not allowed: {hostname}")
        
        # 169.254.0.0/16 (link-local)
        if hostname_lower.startswith('169.254.'):
            raise ValueError(f"Access to private/local networks is not allowed: {hostname}")
