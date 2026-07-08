import hashlib


def hash_ip(ip: str, salt: str) -> str | None:
    """Salted one-way hash of a client IP for abuse correlation.

    Returns None when no salt is configured, so we never persist a bare,
    trivially-reversible hash of a raw address.
    """
    if not salt:
        return None
    return hashlib.sha256(f"{salt}:{ip}".encode("utf-8")).hexdigest()
