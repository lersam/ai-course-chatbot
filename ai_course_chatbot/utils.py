"""
Utility functions for URL validation and security
"""
from urllib.parse import urlparse
import ipaddress
import socket


def validate_url_safety(url: str) -> None:
    """
    Validate that a URL is safe to access (no SSRF attacks).
    Raises ValueError if the URL is not safe.
    """
    parsed = urlparse(url)
    
    # Only allow http and https schemes
    if parsed.scheme not in ('http', 'https'):
        raise ValueError(f"Invalid URL scheme: {parsed.scheme}. Only http and https are allowed.")
    
    # Get the hostname
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL must have a valid hostname")
    
    try:
        # Resolve hostname to IP address(es)
        # This prevents bypasses using alternative representations
        addr_info = socket.getaddrinfo(hostname, None)
        
        for family, _, _, _, sockaddr in addr_info:
            ip_str = sockaddr[0]
            
            # Parse the IP address using ipaddress module
            ip = ipaddress.ip_address(ip_str)
            
            # Check if the IP is private, loopback, link-local, or reserved
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                raise ValueError(f"Access to private/local networks is not allowed: {hostname} resolves to {ip}")
            
            # Additional check for multicast and other special addresses
            if ip.is_multicast:
                raise ValueError(f"Access to multicast addresses is not allowed: {hostname} resolves to {ip}")
                
    except socket.gaierror:
        # DNS resolution failed
        raise ValueError(f"Failed to resolve hostname: {hostname}")
    except ValueError as e:
        # Re-raise ValueError from our validation or ipaddress parsing
        if "Access to" in str(e) or "Invalid URL" in str(e) or "URL must have" in str(e) or "Failed to resolve" in str(e):
            raise
        # Invalid IP address format
        raise ValueError(f"Invalid IP address format for hostname: {hostname}")

