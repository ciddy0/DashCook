import ipaddress
import socket
import urllib.parse

MAX_URL_LENGTH = 2048
ALLOWED_SCHEMES = {"http", "https"}


def validate_url(url: str) -> None:
    """
    validate a url before making an http request.
    raises ValueError with a descriptive message on any violation.
    """
    if len(url) > MAX_URL_LENGTH:
        raise ValueError(f"URL exceeds maximum allowed length of {MAX_URL_LENGTH} characters")

    parsed = urllib.parse.urlparse(url)

    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise ValueError(
            f"URL scheme '{parsed.scheme}' is not allowed. Only http and https are permitted"
        )

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL must include a valid hostname")

    try:
        ip_str = socket.getaddrinfo(hostname, None)[0][4][0]
    except socket.gaierror:
        raise ValueError(f"Could not resolve hostname: '{hostname}'")

    ip = ipaddress.ip_address(ip_str)
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
        raise ValueError("Requests to private or internal IP addresses are not allowed")
